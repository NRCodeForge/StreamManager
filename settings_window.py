# Datei: settings_window.py

import tkinter as tk
from tkinter import messagebox, font
import json
import os
import sys


# --- Pfad-Hilfsfunktion ---
def get_path(relative_path):
    """Ermittelt den korrekten Pfad für Ressourcen, egal ob als Skript oder als .exe ausgeführt."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- Design-Konfiguration ---
class Style:
    BACKGROUND = "#1A1B26"
    WIDGET_BG = "#2A2C3A"
    FOREGROUND = "#E0E0E0"
    TEXT_MUTED = "#A6B0CF"
    BORDER = "#4D5166"
    ACCENT_PURPLE = "#8A3FFC"
    ACCENT_BLUE = "#33B1FF"
    FONT_FAMILY = "Roboto"

    @staticmethod
    def get_font(size, bold=False):
        weight = "bold" if bold else "normal"
        try:
            return font.Font(family=Style.FONT_FAMILY, size=size, weight=weight)
        except tk.TclError:
            print(f"Warnung: '{Style.FONT_FAMILY}' nicht gefunden. Nutze Fallback 'Arial'.")
            return font.Font(family="Arial", size=size, weight=weight)


# --- Widget: Moderner Toggle Switch ---
class ToggleSwitch(tk.Canvas):
    def __init__(self, parent, variable, **kwargs):
        super().__init__(parent, width=50, height=28, bg=Style.BACKGROUND, highlightthickness=0, **kwargs)
        self.variable = variable
        self.variable.trace_add("write", self._update_display)
        self.bind("<Button-1>", self._toggle)
        self.track_coords = (3, 3, 47, 25)
        self.handle_off_coords = (4, 4, 24, 24)
        self.handle_on_coords = (26, 4, 46, 24)
        self.track = self.create_oval(self.track_coords, outline="", fill=Style.BORDER)
        self.handle = self.create_oval(self.handle_off_coords, outline="", fill="white")
        self._update_display()

    def _toggle(self, event=None):
        self.variable.set(not self.variable.get())

    def _update_display(self, *args):
        if self.variable.get():
            self.itemconfig(self.track, fill=Style.ACCENT_PURPLE)
            self.coords(self.handle, self.handle_on_coords)
        else:
            self.itemconfig(self.track, fill=Style.BORDER)
            self.coords(self.handle, self.handle_off_coords)


# --- Hauptklasse für das Einstellungsfenster ---
class SettingsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Subathon Overlay Einstellungen")
        self.geometry("550x550")
        self.resizable(False, False)
        self.configure(bg=Style.BACKGROUND)
        self.transient(master)
        self.grab_set()

        self.settings_vars = {
            "animations_time": {"value": tk.StringVar()},  # Kein "active" mehr nötig
            "coins": {"value": tk.StringVar(), "active": tk.BooleanVar()},
            "subscribe": {"value": tk.StringVar(), "active": tk.BooleanVar()},
            "follow": {"value": tk.StringVar(), "active": tk.BooleanVar()},
            "share": {"value": tk.StringVar(), "active": tk.BooleanVar()},
            "like": {"value": tk.StringVar(), "active": tk.BooleanVar()},
            "chat": {"value": tk.StringVar(), "active": tk.BooleanVar()}
        }

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=Style.BACKGROUND)
        main_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Timer-Einstellungen für Subathon", font=Style.get_font(18, True),
                 bg=Style.BACKGROUND, fg=Style.FOREGROUND).pack(pady=(0, 5))
        separator = tk.Frame(main_frame, height=2, bg=Style.BORDER)
        separator.pack(fill=tk.X, padx=50, pady=(0, 20))

        grid_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        grid_frame.pack(fill=tk.X, padx=20)
        grid_frame.columnconfigure(1, weight=1)

        labels = {
            "animations_time": "Animations-Dauer (in s):",
            "coins": "Pro Münze (Coin):",
            "subscribe": "Pro Abo / Super Fan:",
            "follow": "Pro Follow:",
            "share": "Pro Teilen (Share):",
            "like": "Pro Like:",
            "chat": "Pro Chat-Nachricht:"
        }

        for i, (key, text) in enumerate(labels.items()):
            tk.Label(grid_frame, text=text, font=Style.get_font(12), bg=Style.BACKGROUND, fg=Style.TEXT_MUTED).grid(
                row=i, column=0, padx=5, pady=10, sticky="w")

            entry = tk.Entry(grid_frame, textvariable=self.settings_vars[key]["value"], font=Style.get_font(12),
                             bg=Style.WIDGET_BG, fg=Style.FOREGROUND, relief=tk.FLAT,
                             insertbackground=Style.FOREGROUND, highlightthickness=1,
                             highlightbackground=Style.BORDER, highlightcolor=Style.ACCENT_PURPLE)
            entry.grid(row=i, column=1, padx=15, pady=10, ipady=5, sticky="ew")

            # HIER IST DIE ANPASSUNG: Nur für andere Elemente einen Toggle erstellen
            if key != "animations_time":
                toggle = ToggleSwitch(grid_frame, variable=self.settings_vars[key]["active"])
                toggle.grid(row=i, column=2, padx=5, pady=10, sticky="e")

        save_button = tk.Button(main_frame, text="Speichern & Schließen", font=Style.get_font(12, bold=True),
                                bg=Style.ACCENT_PURPLE, fg="white", relief=tk.FLAT, borderwidth=0,
                                activebackground=Style.ACCENT_BLUE, activeforeground="white",
                                command=self.save_and_close)
        save_button.pack(side=tk.BOTTOM, pady=20, ipady=8, ipadx=15, fill=tk.X, padx=20)

    def save_and_close(self):
        self.save_settings()
        self.destroy()

    def save_settings(self):
        """Speichert den Wert und den Aktiv-Status für jedes Element."""
        settings_to_save = {}

        # Animationszeit immer speichern
        settings_to_save["animations_time"] = self.settings_vars["animations_time"]["value"].get()

        # Für alle anderen Elemente den Wert UND den Status speichern
        for key, var_dict in self.settings_vars.items():
            if key != "animations_time":
                settings_to_save[key] = {
                    "value": var_dict["value"].get(),
                    "active": var_dict["active"].get()
                }

        try:
            settings_path = get_path('subathon_overlay/settings.json')
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w') as f:
                json.dump(settings_to_save, f, indent=4)
            messagebox.showinfo("Gespeichert", "Einstellungen wurden erfolgreich gespeichert.", parent=self)
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern der Einstellungen:\n{e}", parent=self)

    def load_settings(self):
        """Lädt den Wert und den Aktiv-Status für jedes Element."""
        default_settings = {
            "animations_time": "1",
            "coins": {"value": "3 Seconds", "active": True},
            "subscribe": {"value": "500 Seconds", "active": True},
            "follow": {"value": "10 Seconds", "active": True},
            "share": {"value": "0.1 Seconds", "active": True},
            "like": {"value": "0.1 Seconds", "active": True},
            "chat": {"value": "0 Seconds", "active": False}
        }

        try:
            settings_path = get_path('subathon_overlay/settings.json')
            if not os.path.exists(settings_path):
                # Wenn keine Datei da ist, Defaults laden
                for key, data in default_settings.items():
                    if key == "animations_time":
                        self.settings_vars[key]["value"].set(data)
                    else:
                        self.settings_vars[key]["value"].set(data["value"])
                        self.settings_vars[key]["active"].set(data["active"])
                return

            with open(settings_path, 'r') as f:
                saved_settings = json.load(f)

            # Gespeicherte Einstellungen laden
            for key, var_dict in self.settings_vars.items():
                saved_data = saved_settings.get(key, default_settings.get(key))

                if key == "animations_time":
                    var_dict["value"].set(saved_data)
                else:
                    var_dict["value"].set(saved_data.get("value", ""))
                    var_dict["active"].set(saved_data.get("active", False))

        except Exception as e:
            messagebox.showerror("Ladefehler", f"Konnte Einstellungen nicht laden, nutze Standardwerte:\n{e}",
                                 parent=self)
            # Fallback auf Defaults bei Fehler
            for key, data in default_settings.items():
                if key == "animations_time":
                    self.settings_vars[key]["value"].set(data)
                else:
                    self.settings_vars[key]["value"].set(data["value"])
                    self.settings_vars[key]["active"].set(data["active"])


# Code zum alleinigen Testen des Fensters
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Hauptfenster (Test)")
    root.withdraw()

    settings_win = SettingsWindow(root)
    root.wait_window(settings_win)