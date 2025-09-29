import threading
import tkinter as tk
from tkinter import messagebox, font
import subprocess
import os
import sys
import requests
from pynput import keyboard
import logging

# Importiere das neue Einstellungsfenster
from settings_window import SettingsWindow


# --- Pfad- und Logging-Konfiguration ---
def get_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def setup_logging():
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
WEB_ELEMENTS = {
    "Killer Wünsche": "killer_wishes/index.html",
    "Subathon Overlay": "subathon_overlay/index.html",
    "Timer Overlay": "timer_overlay/index.html"
}
BASE_URL = 'http://127.0.0.1:5000/'
NEXT_KILLER_URL = f'{BASE_URL}killer_wishes/next'
RESET_DATABASE_URL = f'{BASE_URL}killer_wishes/reset'

app_process = None
is_server_running = False


# --- Design-Konfiguration ---
class Style:
    BACKGROUND = "#1c1c1c"
    FOREGROUND = "#e0e0e0"
    ACCENT = "#ff4500"
    WIDGET_BG = "#2a2a2a"
    FONT_FAMILY = "Bebas Neue"

    @staticmethod
    def get_font(size, bold=False):
        weight = "bold" if bold else "normal"
        try:
            return font.Font(family=Style.FONT_FAMILY, size=size, weight=weight)
        except tk.TclError:
            return font.Font(family="Arial", size=size, weight=weight)


# --- UI- und Server-Logik ---
def start_webserver():
    global app_process, is_server_running
    if is_server_running:
        server_log.warning("Server-Startversuch, obwohl er bereits läuft.")
        return

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        server_path = os.path.join(base_dir, "webserver.exe")
    else:
        server_path = os.path.join(os.path.dirname(__file__), "app.py")

    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        app_process = subprocess.Popen([sys.executable if not server_path.endswith(".exe") else server_path] +
                                       ([server_path] if not server_path.endswith(".exe") else []),
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
        server_log.info("Versuche, den Server zu stoppen.")
        try:
            app_process.terminate()
            app_process.wait(timeout=5)
            server_log.info("Server-Prozess erfolgreich beendet.")
        except subprocess.TimeoutExpired:
            server_log.warning("Server-Prozess hat nicht rechtzeitig reagiert und wird gekillt.")
            app_process.kill()
        except Exception as e:
            server_log.error(f"Fehler beim Stoppen des Servers: {e}")
        finally:
            app_process = None
            is_server_running = False
            update_status("Server: OFFLINE", "red")


def on_app_close():
    if is_server_running:
        stop_server_action()
    root.destroy()


def copy_url_to_clipboard(url):
    root.clipboard_clear()
    root.clipboard_append(url)
    messagebox.showinfo("URL kopiert", f"'{url}' wurde in die Zwischenablage kopiert.")


def reset_database_action():
    if not is_server_running:
        messagebox.showerror("Fehler", "Server ist nicht aktiv.")
        return
    if messagebox.askyesno("Bestätigen",
                           "Bist du sicher, dass du alle Killer-Wünsche unwiderruflich löschen möchtest?"):
        try:
            response = requests.post(RESET_DATABASE_URL)
            if response.status_code == 200:
                messagebox.showinfo("Erfolg", "Datenbank erfolgreich zurückgesetzt.")
            else:
                messagebox.showerror("Fehler", f"Fehler beim Zurücksetzen: {response.text}")
        except requests.exceptions.RequestException:
            messagebox.showerror("Fehler", "Konnte keine Verbindung zum Server herstellen.")


def open_settings_window():
    SettingsWindow(root)


def on_press(key):
    try:
        if key == keyboard.Key.page_down:
            if not is_server_running:
                server_log.warning("Hotkey ausgelöst, aber Server ist inaktiv.")
                return
            try:
                response = requests.post(NEXT_KILLER_URL)
                if response.status_code == 200:
                    server_log.info(f"Hotkey 'Bild Runter' erfolgreich: {response.json().get('message')}")
                else:
                    server_log.error(f"Hotkey 'Bild Runter' FEHLER: Status {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                server_log.error(f"Hotkey 'Bild Runter' FEHLER: Konnte keine Verbindung zum Server herstellen. {e}")
    except Exception:
        pass


listener_thread = threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).start(), daemon=True)
listener_thread.start()


def update_status(message, color):
    status_label.config(text=message, fg=color)


# --- GUI-Setup ---
root = tk.Tk()
root.title("Stream Overlay Manager")
root.geometry("600x480")
root.resizable(False, False)
root.configure(bg=Style.BACKGROUND)

# Server Status Frame
server_frame = tk.Frame(root, bg=Style.BACKGROUND)
server_frame.pack(pady=20, fill=tk.X)
title_container = tk.Frame(server_frame, bg=Style.BACKGROUND)
title_container.pack()
server_title_label = tk.Label(title_container, text="Serverstatus:", font=Style.get_font(20, True), bg=Style.BACKGROUND,
                              fg=Style.FOREGROUND)
server_title_label.pack(side=tk.LEFT, padx=10)
status_label = tk.Label(title_container, text="Server: OFFLINE", fg="red", font=Style.get_font(20, True),
                        bg=Style.BACKGROUND)
status_label.pack(side=tk.LEFT, padx=20)
separator1 = tk.Frame(server_frame, height=2, bg=Style.ACCENT)
separator1.pack(fill=tk.X, padx=50, pady=(10, 0))

# URLs Frame
url_frame = tk.Frame(root, bg=Style.BACKGROUND)
url_frame.pack(pady=20, padx=20, fill=tk.X)
tk.Label(url_frame, text="Web-Elemente URLs", font=Style.get_font(18, True), bg=Style.BACKGROUND,
         fg=Style.FOREGROUND).pack(pady=(0, 5))
separator2 = tk.Frame(url_frame, height=2, bg=Style.ACCENT)
separator2.pack(fill=tk.X, padx=50, pady=(0, 15))

for name, path in WEB_ELEMENTS.items():
    container = tk.Frame(url_frame, bg=Style.BACKGROUND)
    container.pack(fill=tk.X, pady=8)
    url = f"{BASE_URL}{path}"

    tk.Label(container, text=f"{name}:", font=Style.get_font(14), bg=Style.BACKGROUND, fg=Style.FOREGROUND).pack(
        side=tk.LEFT, padx=5)

    url_entry = tk.Entry(container, width=50, font=Style.get_font(12), readonlybackground=Style.WIDGET_BG,
                         fg=Style.FOREGROUND, relief=tk.FLAT, borderwidth=2, highlightthickness=1,
                         highlightbackground=Style.ACCENT)
    url_entry.insert(0, url)
    url_entry.config(state='readonly')
    url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=5)

    copy_button = tk.Button(container, text="Kopieren", font=Style.get_font(11), bg=Style.ACCENT, fg=Style.BACKGROUND,
                            relief=tk.FLAT, activebackground="#ff6a33", activeforeground=Style.BACKGROUND,
                            borderwidth=0, command=lambda u=url: copy_url_to_clipboard(u))
    copy_button.pack(side=tk.LEFT, padx=5, ipady=2, ipadx=5)

    if "Subathon" in name:
        settings_button = tk.Button(container, text="⚙️", font=Style.get_font(11), bg=Style.WIDGET_BG,
                                    fg=Style.FOREGROUND,
                                    relief=tk.FLAT, command=open_settings_window)
        settings_button.pack(side=tk.LEFT, padx=(0, 5), ipady=2)

# Aktionen Frame
killer_frame = tk.Frame(root, bg=Style.BACKGROUND)
killer_frame.pack(pady=20, padx=20)
reset_button = tk.Button(killer_frame, text="Killer-Wünsche Datenbank resetten", font=Style.get_font(12),
                         bg=Style.WIDGET_BG, fg=Style.ACCENT, relief=tk.FLAT, borderwidth=1,
                         activebackground=Style.ACCENT, activeforeground=Style.WIDGET_BG, command=reset_database_action)
reset_button.pack(pady=10, ipady=5, ipadx=10)
hotkey_label = tk.Label(killer_frame, text="Hotkey: Drücke 'Bild Runter' für den nächsten Wunsch",
                        font=Style.get_font(11), bg=Style.BACKGROUND, fg=Style.FOREGROUND)
hotkey_label.pack(pady=10)

# --- Start der Anwendung ---
if __name__ == '__main__':
    from database_setup import setup_database

    db_path = get_path('killerwuensche.db')
    setup_database(db_path)
    start_webserver()
    root.protocol("WM_DELETE_WINDOW", on_app_close)
    root.mainloop()