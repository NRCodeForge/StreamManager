# Datei: stream_overlay_manager.py

import threading
import tkinter as tk
from tkinter import messagebox, font
import subprocess
import os
import sys
import requests
from pynput import keyboard
import logging

# Versuche, das Einstellungsfenster zu importieren
try:
    from settings_window import SettingsWindow
except ImportError:
    print("Hinweis: 'settings_window.py' nicht gefunden. Der Einstellungs-Button hat keine Funktion.")


    # Fallback, falls die Datei fehlt, damit das Programm nicht abstürzt
    class SettingsWindow:
        def __init__(self, master):
            print("SettingsWindow-Platzhalter: Fenster würde sich hier öffnen.")
            messagebox.showinfo("Platzhalter", "Dies würde das Einstellungsfenster öffnen.")


# --- Pfad- und Logging-Konfiguration ---
def get_path(relative_path):
    """Ermittelt den korrekten Pfad für Ressourcen, egal ob als Skript oder als .exe ausgeführt."""
    try:
        # Pfad im PyInstaller-Bundle
        base_path = sys._MEIPASS
    except Exception:
        # Pfad im normalen Python-Skript
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def setup_logging():
    """Konfiguriert das Logging in eine Datei."""
    log_path = get_path('server.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    server_logger = logging.getLogger('server_logger')
    server_logger.setLevel(logging.INFO)
    server_handler = logging.FileHandler(log_path)
    server_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    server_logger.addHandler(server_handler)
    return server_logger


server_log = setup_logging()

# --- Globale Variablen und Konstanten ---
BASE_URL = 'http://127.0.0.1:5000/'
NEXT_KILLER_URL = f'{BASE_URL}killer_wishes/next'
RESET_DATABASE_URL = f'{BASE_URL}killer_wishes/reset'
HOTKEY_INFO_TEXT = "Hotkey: Drücke 'Bild Runter' für den nächsten Wunsch"

app_process = None
is_server_running = False


# --- Design-Konfiguration ---
class Style:
    BACKGROUND = "#1A1B26"
    WIDGET_BG = "#2A2C3A"
    WIDGET_HOVER = "#36394A"
    FOREGROUND = "#E0E0E0"
    TEXT_MUTED = "#A6B0CF"
    BORDER = "#4D5166"
    ACCENT_PURPLE = "#8A3FFC"
    ACCENT_BLUE = "#33B1FF"
    SUCCESS = "#42B883"
    DANGER = "#FA4D56"
    FONT_FAMILY = "Roboto"

    @staticmethod
    def get_font(size, bold=False, italic=False):
        weight = "bold" if bold else "normal"
        slant = "italic" if italic else "roman"
        try:
            return font.Font(family=Style.FONT_FAMILY, size=size, weight=weight, slant=slant)
        except tk.TclError:
            print(f"Warnung: '{Style.FONT_FAMILY}' nicht gefunden. Nutze Fallback 'Arial'.")
            return font.Font(family="Arial", size=size, weight=weight, slant=slant)


# --- Helfer-Funktion: Toast Notification ---
def show_toast(root, message):
    """Zeigt eine 5-Sekunden-Benachrichtigung oben rechts an."""
    toast = tk.Toplevel(root)
    toast.wm_overrideredirect(True)
    toast.config(bg=Style.SUCCESS, padx=10, pady=5)

    label = tk.Label(toast, text=message, font=Style.get_font(10, bold=True), bg=Style.SUCCESS, fg="#FFFFFF")
    label.pack()

    root.update_idletasks()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    toast_width = toast.winfo_width()

    x = root_x + root_width - toast_width - 20
    y = root_y + 20

    toast.geometry(f"+{x}+{y}")
    toast.attributes("-topmost", True)

    root.after(3000, toast.destroy)


# --- Haupt-UI-Klasse: UIElementCard ---
class UIElementCard(tk.Frame):
    """Eine wiederverwendbare Karte für jedes UI-Element."""

    def __init__(self, parent, name, url, has_settings=False, has_reset=False, settings_func=None, reset_func=None):
        super().__init__(parent, bg=Style.WIDGET_BG, padx=20, pady=15, highlightbackground=Style.BORDER,
                         highlightthickness=1)

        self.url = url
        self.root = parent.winfo_toplevel()

        self.button_style = {"font": Style.get_font(12), "relief": tk.FLAT, "borderwidth": 0, "bg": Style.WIDGET_BG,
                             "activebackground": Style.WIDGET_HOVER}

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)

        self.name_label = tk.Label(self, text=name, font=Style.get_font(16, bold=True), bg=Style.WIDGET_BG,
                                   fg=Style.FOREGROUND)
        self.name_label.grid(row=0, column=0, sticky="w")

        self.copy_button = tk.Button(self, text="📋", fg=Style.ACCENT_BLUE, **self.button_style,
                                     command=self._on_copy_click)
        self.copy_button.grid(row=0, column=3, sticky="e", padx=(5, 0))

        if has_settings:
            self.settings_button = tk.Button(self, text="⚙️", fg=Style.TEXT_MUTED, **self.button_style,
                                             command=settings_func)
            self.settings_button.grid(row=0, column=2, sticky="e", padx=(5, 0))
            self._bind_hover_color(self.settings_button, Style.ACCENT_PURPLE, Style.TEXT_MUTED)

        if has_reset:
            self.reset_button = tk.Button(self, text="🗑️", fg=Style.DANGER, **self.button_style, command=reset_func)
            self.reset_button.grid(row=0, column=1, sticky="e", padx=(10, 0))
            self._bind_hover_color(self.reset_button, Style.DANGER, Style.DANGER)

        self._bind_hover_effect_to_all()
        self._bind_hover_color(self.copy_button, Style.ACCENT_BLUE, Style.ACCENT_BLUE)

    def _on_enter(self, event):
        self.config(bg=Style.WIDGET_HOVER)
        for widget in self.winfo_children():
            widget.config(bg=Style.WIDGET_HOVER)

    def _on_leave(self, event):
        self.config(bg=Style.WIDGET_BG)
        for widget in self.winfo_children():
            widget.config(bg=Style.WIDGET_BG)

    def _bind_hover_color(self, widget, enter_fg, leave_fg):
        widget.bind("<Enter>", lambda e, w=widget, c=enter_fg: w.config(fg=c), add='+')
        widget.bind("<Leave>", lambda e, w=widget, c=leave_fg: w.config(fg=c), add='+')

    def _bind_hover_effect_to_all(self):
        widgets = [self] + self.winfo_children()
        for widget in widgets:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_copy_click(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.url)
        show_toast(self.root, "In Zwischenablage kopiert")


# --- UI- und Server-Logik ---
def start_webserver():
    global app_process, is_server_running
    if is_server_running: return

    server_path = get_path("webserver.exe" if getattr(sys, 'frozen', False) else "app.py")

    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        command = [server_path] if server_path.endswith(".exe") else [sys.executable, server_path]
        app_process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       creationflags=creationflags)
        is_server_running = True
        update_status("Server: ONLINE", "#00ff00")
        server_log.info("Webserver erfolgreich gestartet.")
    except Exception as e:
        server_log.error(f"Fehler beim Starten des Webservers: {e}")
        update_status("Server: FEHLER", "red")


def stop_server_action():
    global app_process, is_server_running
    if is_server_running and app_process:
        try:
            app_process.terminate()
            app_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            app_process.kill()
        except Exception as e:
            server_log.error(f"Fehler beim Stoppen des Servers: {e}")
        finally:
            app_process = None
            is_server_running = False
            update_status("Server: OFFLINE", "red")
            server_log.info("Server gestoppt.")


def on_app_close():
    stop_server_action()
    root.destroy()


def reset_database_action():
    if not is_server_running:
        messagebox.showerror("Fehler", "Server ist nicht aktiv.")
        return
    if messagebox.askyesno("Bestätigen",
                           "Bist du sicher, dass du alle Killer-Wünsche unwiderruflich löschen möchtest?"):
        try:
            response = requests.post(RESET_DATABASE_URL)
            response.raise_for_status()
            messagebox.showinfo("Erfolg", "Datenbank erfolgreich zurückgesetzt.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Fehler", f"Serverfehler: {e}")


def open_settings_window():
    if 'root' in globals():
        SettingsWindow(root)


def on_press(key):
    try:
        if key == keyboard.Key.page_down and is_server_running:
            requests.post(NEXT_KILLER_URL)
    except Exception as e:
        server_log.error(f"Hotkey-Fehler: {e}")


def update_status(message, color):
    if 'status_label' in globals():
        status_label.config(text=message, fg=color)


# --- Anwendung starten ---
if __name__ == '__main__':
    # Listener in einem separaten Thread starten
    listener_thread = threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).start(), daemon=True)
    listener_thread.start()

    # Konfiguration der UI-Elemente
    UI_ELEMENTS_CONFIG = [
        {"name": "Wishlist", "path": "killer_wishes/index.html", "has_settings": False, "has_reset": True,
         "reset_func": reset_database_action},
        {"name": "Subathon Overlay", "path": "subathon_overlay/index.html", "has_settings": True,
         "settings_func": open_settings_window, "has_reset": False},
        {"name": "Timer Overlay", "path": "timer_overlay/index.html", "has_settings": False, "has_reset": False}
    ]

    # --- GUI-Setup ---
    root = tk.Tk()
    root.title("Stream Overlay Manager")
    root.geometry("600x480")
    root.resizable(False, False)
    root.configure(bg=Style.BACKGROUND)
    root.protocol("WM_DELETE_WINDOW", on_app_close)

    # Server Status Frame (Oben)
    server_frame = tk.Frame(root, bg=Style.BACKGROUND)
    server_frame.pack(pady=(20, 10), padx=20, fill=tk.X)
    server_frame.columnconfigure(0, weight=1)
    tk.Label(server_frame, text="Serverstatus:", font=Style.get_font(20, True), bg=Style.BACKGROUND,
             fg=Style.FOREGROUND).pack(side=tk.LEFT, padx=(0, 10))
    status_label = tk.Label(server_frame, text="Server: OFFLINE", fg="red", font=Style.get_font(20, True),
                            bg=Style.BACKGROUND)
    status_label.pack(side=tk.LEFT)

    # Trennlinie
    separator1 = tk.Frame(root, height=2, bg=Style.BORDER)
    separator1.pack(fill=tk.X, padx=50, pady=(10, 20))

    # Element Manager Frame (Mitte)
    element_manager_frame = tk.Frame(root, bg=Style.BACKGROUND)
    element_manager_frame.pack(pady=10, padx=30, fill=tk.X)

    for config in UI_ELEMENTS_CONFIG:
        url = f"{BASE_URL}{config['path']}"
        card = UIElementCard(parent=element_manager_frame, name=config["name"], url=url,
                             **{k: v for k, v in config.items() if k not in ["name", "path"]})
        card.pack(fill=tk.X, pady=6)

    # Hotkey Frame (Unten)
    hotkey_frame = tk.Frame(root, bg=Style.BACKGROUND)
    hotkey_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
    hotkey_label = tk.Label(hotkey_frame, text=HOTKEY_INFO_TEXT, font=Style.get_font(11, italic=True),
                            bg=Style.BACKGROUND, fg=Style.TEXT_MUTED)
    hotkey_label.pack()

    # Datenbank-Setup (falls nötig)
    try:
        from database_setup import setup_database

        db_path = get_path('killerwuensche.db')
        setup_database(db_path)
    except ImportError:
        print("Hinweis: 'database_setup.py' nicht gefunden. Überspringe Datenbank-Setup.")
    except Exception as e:
        print(f"Fehler beim Datenbank-Setup: {e}")

    # Server verzögert starten, damit das UI zuerst laden kann
    root.after(100, start_webserver)

    root.mainloop()