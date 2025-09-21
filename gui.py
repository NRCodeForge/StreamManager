import tkinter as tk
from tkinter import messagebox
import threading
import subprocess
import os
import sys
import requests
from pynput import keyboard
from PIL import Image, ImageTk
import logging
import time


# --- Pfad- und Logging-Konfiguration ---
# Bestimmt den korrekten Pfad, wenn die App als PyInstaller-Bundle ausgeführt wird
def get_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def setup_logging():
    server_logger = logging.getLogger('server_logger')
    server_logger.setLevel(logging.INFO)
    server_handler = logging.FileHandler(get_path('server.log'))
    server_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    server_logger.addHandler(server_handler)

    wishes_logger = logging.getLogger('wishes_logger')
    wishes_logger.setLevel(logging.INFO)
    wishes_handler = logging.FileHandler(get_path('wishes.log'))
    wishes_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    wishes_logger.addHandler(wishes_handler)

    return server_logger, wishes_logger


server_log, wishes_log = setup_logging()

# --- Globale Variablen und Konstanten ---
WEB_ELEMENTS = {
    "Killer Wünsche": "killer_wishes/index.html",
    "Subathon Overlay": "subathon_overlay/index.html"
}
BASE_URL = 'http://127.0.0.1:5000/'
NEXT_KILLER_URL = f'{BASE_URL}killer_wishes/next'
RESET_DATABASE_URL = f'{BASE_URL}killer_wishes/reset'

app_process = None
is_server_running = False


# --- UI- und Server-Logik ---
def start_webserver():
    if getattr(sys, 'frozen', False):
        # Beide EXEs im selben dist-Ordner
        base_dir = os.path.dirname(sys.executable)
        server_path = os.path.join(base_dir, "webserver.exe")
    else:
        # Dev-Modus
        server_path = os.path.join(os.path.dirname(__file__), "app.py")

    try:
        if server_path.endswith(".exe"):
            subprocess.Popen([server_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen([sys.executable, server_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Fehler beim Starten des Webservers: {e}")



def stop_server_action():
    """Stoppt den Flask-Server-Prozess."""
    global app_process, is_server_running
    if is_server_running and app_process:
        server_log.info("Versuche, den Server zu stoppen.")
        try:
            app_process.terminate()
            app_process.wait()
            is_server_running = False
            update_status("Server: OFFLINE", "red")
            server_log.info("Server-Prozess erfolgreich beendet.")
        except Exception as e:
            update_status(f"Server: FEHLER", "red")
            server_log.error(f"Fehler beim Stoppen: {e}")


def copy_url_to_clipboard(url):
    """Kopiert eine URL in die Zwischenablage."""
    root.clipboard_clear()
    root.clipboard_append(url)
    messagebox.showinfo("URL kopiert", f"'{url}' wurde in die Zwischenablage kopiert.")


def reset_database_action():
    """Sendet eine POST-Anfrage zum Zurücksetzen der Datenbank."""
    if not is_server_running:
        messagebox.showerror("Fehler", "Server ist nicht aktiv.")
        return

    try:
        response = requests.post(RESET_DATABASE_URL)
        if response.status_code == 200:
            messagebox.showinfo("Erfolg", "Datenbank erfolgreich zurückgesetzt.")
        else:
            messagebox.showerror("Fehler", f"Fehler beim Zurücksetzen: {response.status_code}")
    except requests.exceptions.RequestException:
        messagebox.showerror("Fehler", "Konnte keine Verbindung zum Server herstellen.")


# Hotkey-Funktionalität
def on_press(key):
    try:
        if key == keyboard.Key.page_down:
            if is_server_running:
                requests.post(NEXT_KILLER_URL)
                server_log.info("Hotkey 'Bild Runter' ausgelöst: Nächster Killer wird angezeigt.")
            else:
                server_log.warning("Hotkey ausgelöst, aber Server ist inaktiv.")
    except AttributeError:
        pass


# Hotkey-Listener in einem separaten Thread
listener_thread = threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).start())
listener_thread.daemon = True
listener_thread.start()


def update_status(message, color):
    status_label.config(text=message, fg=color)


# --- GUI-Setup ---
root = tk.Tk()
root.title("Stream-Overlay Manager")
root.geometry("550x400")
root.resizable(False, False)

# Server-Steuerung (oben)
server_frame = tk.Frame(root)
server_frame.pack(pady=10)

server_title_label = tk.Label(server_frame, text="Serverstatus:", font=("Arial", 14, "bold"))
server_title_label.pack(side=tk.LEFT, padx=10)

status_label = tk.Label(server_frame, text="Server: OFFLINE", fg="red", font=("Arial", 14, "bold"))
status_label.pack(side=tk.LEFT, padx=20)

# URL-Liste (Mitte)
url_frame = tk.Frame(root)
url_frame.pack(pady=20, padx=20)

tk.Label(url_frame, text="Web-Elemente URLs:", font=("Arial", 14, "bold")).pack(pady=(0, 10))

for name, path in WEB_ELEMENTS.items():
    container = tk.Frame(url_frame)
    container.pack(fill=tk.X, pady=5)

    url = f"{BASE_URL}{path}"

    tk.Label(container, text=f"{name}:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

    url_entry = tk.Entry(container, width=50)
    url_entry.insert(0, url)
    url_entry.config(state='readonly')
    url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    copy_button = tk.Button(container, text="Kopieren", command=lambda u=url: copy_url_to_clipboard(u))
    copy_button.pack(side=tk.LEFT, padx=5)

# Killer-Wünsche Steuerung (unten)
killer_frame = tk.Frame(root)
killer_frame.pack(pady=10)

reset_button = tk.Button(killer_frame, text="Killer-Wünsche Datenbank resetten", command=reset_database_action)
reset_button.pack(pady=5)

hotkey_label = tk.Label(killer_frame, text="Hotkey: Drücke 'Bild Runter' für den nächsten Wunsch.")
hotkey_label.pack(pady=5)

# Start der Anwendung
if __name__ == '__main__':
    from database_setup import setup_database

    db_path = get_path('killerwuensche.db')
    setup_database(db_path)

    # Server automatisch im Hintergrund starten
    start_webserver()


    root.mainloop()

    # Stellt sicher, dass der Server-Prozess beendet wird, wenn das Fenster geschlossen wird
    if is_server_running and app_process:
        stop_server_action()