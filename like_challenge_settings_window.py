import tkinter as tk
from tkinter import messagebox, font
import json
import os
import sys


# --- Pfad-Hilfsfunktion ---
def get_path(relative_path):
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
            return font.Font(family="Arial", size=size, weight=weight)


class LikeChallengeSettingsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Like Challenge Einstellungen")
        self.geometry("600x450")
        self.resizable(False, False)
        self.configure(bg=Style.BACKGROUND)
        self.transient(master)
        self.grab_set()

        self.settings_vars = {
            "widgetUrl": tk.StringVar(),
            "initialGoals": tk.StringVar(),
            "recurringGoalExpression": tk.StringVar(),
            "displayTextFormat": tk.StringVar()
        }

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=Style.BACKGROUND)
        main_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Einstellungen für Like Challenge", font=Style.get_font(18, True),
                 bg=Style.BACKGROUND, fg=Style.FOREGROUND).pack(pady=(0, 5))
        separator = tk.Frame(main_frame, height=2, bg=Style.BORDER)
        separator.pack(fill=tk.X, padx=50, pady=(0, 20))

        grid_frame = tk.Frame(main_frame, bg=Style.BACKGROUND)
        grid_frame.pack(fill=tk.X, padx=20)
        grid_frame.columnconfigure(1, weight=1)

        labels = {
            "widgetUrl": "Tikfinity Widget URL:",
            "initialGoals": "Initiale Ziele (kommagetrennt):",
            "recurringGoalExpression": "Wiederkehrende Formel (mit 'x'):",
            "displayTextFormat": "Anzeigetext (nutze {likes_needed}):"
        }

        for i, (key, text) in enumerate(labels.items()):
            tk.Label(grid_frame, text=text, font=Style.get_font(12), bg=Style.BACKGROUND, fg=Style.TEXT_MUTED).grid(
                row=i, column=0, padx=5, pady=10, sticky="w")
            entry = tk.Entry(grid_frame, textvariable=self.settings_vars[key], font=Style.get_font(12),
                             bg=Style.WIDGET_BG, fg=Style.FOREGROUND, relief=tk.FLAT,
                             insertbackground=Style.FOREGROUND, highlightthickness=1,
                             highlightbackground=Style.BORDER, highlightcolor=Style.ACCENT_PURPLE)
            entry.grid(row=i, column=1, padx=15, pady=10, ipady=5, sticky="ew")

        save_button = tk.Button(main_frame, text="Speichern & Schließen", font=Style.get_font(12, bold=True),
                                bg=Style.ACCENT_PURPLE, fg="white", relief=tk.FLAT, borderwidth=0,
                                activebackground=Style.ACCENT_BLUE, activeforeground="white",
                                command=self.save_and_close)
        save_button.pack(side=tk.BOTTOM, pady=20, ipady=8, ipadx=15, fill=tk.X, padx=20)

    def save_and_close(self):
        try:
            settings_to_save = {
                "widgetUrl": self.settings_vars["widgetUrl"].get(),
                "initialGoals": [int(goal.strip()) for goal in self.settings_vars["initialGoals"].get().split(',')],
                "recurringGoalExpression": self.settings_vars["recurringGoalExpression"].get(),
                "displayTextFormat": self.settings_vars["displayTextFormat"].get()
            }
            settings_path = get_path('like_challenge_overlay/settings.json')
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=4)
            messagebox.showinfo("Gespeichert", "Einstellungen wurden erfolgreich gespeichert.", parent=self)
            self.destroy()
        except ValueError:
            messagebox.showerror("Fehler",
                                 "Bitte gib die initialen Ziele als kommagetrennte Zahlen ein (z.B. 10000, 20000).",
                                 parent=self)
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern der Einstellungen:\n{e}", parent=self)

    def load_settings(self):
        try:
            settings_path = get_path('like_challenge_overlay/settings.json')
            if not os.path.exists(settings_path):
                # Standardwerte, falls keine Datei existiert
                self.settings_vars["widgetUrl"].set("https://tikfinity.zerody.one/widget/goal?cid=2093691&metric=likes")
                self.settings_vars["initialGoals"].set("10000, 20000, 40000, 80000, 100000")
                self.settings_vars["recurringGoalExpression"].set("x + 33333")
                self.settings_vars["displayTextFormat"].set("{likes_needed} Likes bis zur Nächsten 20er Geschenktüte")
                return

            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            self.settings_vars["widgetUrl"].set(settings.get("widgetUrl", ""))
            self.settings_vars["initialGoals"].set(", ".join(map(str, settings.get("initialGoals", []))))
            self.settings_vars["recurringGoalExpression"].set(settings.get("recurringGoalExpression", "x + 33333"))
            self.settings_vars["displayTextFormat"].set(settings.get("displayTextFormat", "{likes_needed} Likes..."))
        except Exception as e:
            messagebox.showerror("Ladefehler", f"Konnte Einstellungen nicht laden:\n{e}", parent=self)