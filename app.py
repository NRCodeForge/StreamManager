import os
import json
import logging
import sqlite3
import sys
import subprocess
import webbrowser
from flask import Flask, render_template, jsonify, request, g
from flask_cors import CORS
import numpy
import requests
from bs4 import BeautifulSoup


# --- Pfad-Hilfsfunktion ---
def get_path(relative_path):
    """Ermittelt den korrekten Pfad für Ressourcen, egal ob als Skript oder als .exe ausgeführt."""
    try:
        # Pfad im PyInstaller-Bundle
        base_path = sys._MEIPASS
    except Exception:
        # Pfad im normalen Python-Skript
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- Logging-Konfiguration ---
def setup_logging():
    """Konfiguriert das Logging in eine Datei."""
    log_path = get_path('server.log')
    # Sicherstellen, dass das Verzeichnis existiert
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    server_logger = logging.getLogger('server_logger')
    server_logger.setLevel(logging.INFO)
    # Verhindert doppelte Handler, falls das Skript neu geladen wird
    if not server_logger.handlers:
        server_handler = logging.FileHandler(log_path, encoding='utf-8')
        server_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        server_logger.addHandler(server_handler)
    return server_logger


server_log = setup_logging()

# --- App-Konfiguration ---
DATABASE = get_path('killerwuensche.db')
# Template-Ordner auf das Basisverzeichnis setzen, damit die Overlays gefunden werden
app = Flask(__name__, template_folder=os.path.abspath("."))
CORS(app)


# --- Datenbank-Helferfunktionen ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# --- Routen für Killer Wishes Overlay ---
@app.route('/killer_wishes/')
def killer_wishes_index():
    return render_template('killer_wishes/index.html')


@app.route('/killer_wishes/data', methods=['GET'])
def get_wishes_data():
    db = get_db()
    cursor = db.execute('SELECT user_name, wunsch FROM killer_wishes ORDER BY id DESC LIMIT 2')
    wishes = [dict(row) for row in cursor.fetchall()]
    return jsonify(wishes)


@app.route('/killer_wishes/next', methods=['POST'])
def next_wish():
    db = get_db()
    cursor = db.execute('SELECT id FROM killer_wishes ORDER BY id ASC LIMIT 1')
    oldest_wish = cursor.fetchone()
    if oldest_wish:
        db.execute('DELETE FROM killer_wishes WHERE id = ?', (oldest_wish['id'],))
        db.commit()
        server_log.info(f"Wunsch mit ID {oldest_wish['id']} durch Hotkey entfernt.")
        return jsonify({"status": "success", "message": "Ältester Wunsch entfernt."}), 200
    return jsonify({"status": "not found", "message": "Keine Wünsche zum Entfernen."}), 404


@app.route('/killer_wishes/reset', methods=['POST'])
def reset_database():
    try:
        db = get_db()
        db.execute('DELETE FROM killer_wishes')
        db.commit()
        server_log.info("Datenbank wurde zurückgesetzt.")
        return jsonify({"status": "success", "message": "Datenbank zurückgesetzt."}), 200
    except Exception as e:
        server_log.error(f"Fehler beim Zurücksetzen der Datenbank: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Routen für Subathon Timer & Rules ---
@app.route('/timer_overlay/')
def timer_overlay_index():
    return render_template('timer_overlay/index.html')


@app.route('/subathon_overlay/')
def subathon_overlay_index():
    return render_template('subathon_overlay/index.html')


# --- Routen für Like Challenge Overlay ---
@app.route('/like_challenge_overlay/')
def like_challenge_index():
    """Stellt die HTML-Seite für das Like Challenge Overlay bereit."""
    return render_template('like_challenge_overlay/index.html')


def evaluate_expression_safely(expression, x_value):
    """Wertet eine mathematische Formel sicher aus, indem numpy verwendet wird."""
    allowed_names = {"x": x_value, "numpy": numpy, "np": numpy}
    if "__" in expression:
        raise ValueError("Ungültiger Ausdruck in der Formel.")
    result = eval(expression, {"__builtins__": {}}, allowed_names)
    return int(result)


@app.route('/like_challenge_data')
def get_like_challenge_data():
    """Holt, berechnet und liefert die Daten für die Like Challenge."""
    try:
        settings_path = get_path('like_challenge_overlay/settings.json')
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)

        widget_url = settings.get("widgetUrl")
        initial_goals = sorted(settings.get("initialGoals", []))
        recurring_expression = settings.get("recurringGoalExpression", "x + 33333")
        display_format = settings.get("displayTextFormat", "{likes_needed} Likes bis zum Ziel")

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(widget_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        goal_element = soup.select_one('.goal-progress-current, #goal-current, .goal-stat-current')
        if not goal_element:
            return jsonify({"error": "Like-Zahl nicht gefunden"}), 500

        current_likes_text = goal_element.get_text(strip=True).replace('.', '').replace(',', '')
        current_likes = int(''.join(filter(str.isdigit, current_likes_text)))

        next_goal = 0
        for goal in initial_goals:
            if current_likes < goal:
                next_goal = goal
                break

        if next_goal == 0:
            last_goal = initial_goals[-1] if initial_goals else 0
            while last_goal <= current_likes:
                last_goal = evaluate_expression_safely(recurring_expression, last_goal)
            next_goal = last_goal

        likes_needed = next_goal - current_likes
        formatted_likes_needed = f"{likes_needed:,}".replace(",", ".")
        display_text = display_format.replace("{likes_needed}", formatted_likes_needed)

        return jsonify({"displayText": display_text})
    except FileNotFoundError:
        return jsonify({"error": "settings.json nicht gefunden"}), 500
    except Exception as e:
        server_log.error(f"Like Challenge Fehler: {e}")
        return jsonify({"error": "Server-Fehler"}), 500


# --- Hauptausführung ---
if __name__ == '__main__':
    # Debug-Modus für die Entwicklung, schalte ihn für die finale Version aus
    # use_reloader=False ist wichtig, damit nicht zwei Serverprozesse gestartet werden.
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)