from flask import Flask, jsonify, send_from_directory, request, g
import sqlite3
import os
import sys
import logging

def get_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__)

# --- Konfiguration ---
DATABASE = get_path('killerwuensche.db')
offset_counter = 0  # Achtung: nicht threadsicher, für kleine App ok

# --- Logging ---
wishes_logger = logging.getLogger('wishes_logger')
wishes_logger.setLevel(logging.INFO)
handler = logging.FileHandler(get_path('wishes.log'))
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
wishes_logger.addHandler(handler)

# --- DB Handling ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db:
        db.close()

# --- API Endpoints ---
@app.route('/killer_wishes/next', methods=['POST'], strict_slashes=False)
def next_killer():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM killer_wuensche WHERE id IN (SELECT id FROM killer_wuensche ORDER BY id ASC LIMIT 1)")
        conn.commit()
        if cursor.rowcount > 0:
            wishes_logger.info('Ältester Wunsch erfolgreich gelöscht (Hotkey).')
            return jsonify({'message': 'Ältester Wunsch erfolgreich gelöscht.'}), 200
        else:
            wishes_logger.info('Keine Wünsche zum Löschen vorhanden (Hotkey).')
            return jsonify({'message': 'Keine Wünsche mehr in der Liste.'}), 200
    except sqlite3.Error as e:
        wishes_logger.error(f'Datenbank-Fehler beim Löschen des nächsten Wunsches: {e}')
        return jsonify({'error': f'Datenbank-Fehler: {e}'}), 500

@app.route('/killerwuensche', methods=['POST'])
def add_killerwunsch():
    data = request.get_json()
    if not data or 'wunsch' not in data or 'user_name' not in data:
        wishes_logger.error('Fehler: Falsches Format beim Hinzufügen eines Wunsches.')
        return jsonify({'error': 'Falsches Format, "wunsch" oder "user_name" fehlt.'}), 400
    wunsch = data['wunsch']
    user_name = data['user_name']
    try:
        conn = get_db()
        conn.execute("INSERT INTO killer_wuensche (wunsch, user_name) VALUES (?, ?)", (wunsch, user_name))
        conn.commit()
        wishes_logger.info(f'Neuer Wunsch hinzugefügt von {user_name}: {wunsch}')
        return jsonify({'message': 'Wunsch erfolgreich hinzugefügt.'}), 201
    except sqlite3.Error as e:
        wishes_logger.error(f'Datenbank-Fehler: {e}')
        return jsonify({'error': f'Datenbank-Fehler: {e}'}), 500

@app.route('/killer_wishes/data', methods=['GET'], strict_slashes=False)
def get_killer_wishes_data():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT wunsch, user_name FROM killer_wuensche ORDER BY id ASC LIMIT 2")
    wuensche = [dict(row) for row in c.fetchall()]
    return jsonify(wuensche)

@app.route('/killer_wishes/reset', methods=['POST'], strict_slashes=False)
def reset_database():
    conn = get_db()
    conn.execute("DELETE FROM killer_wuensche")
    conn.commit()
    return jsonify({'message': 'Datenbank erfolgreich zurückgesetzt.'}), 200

# --- Statische Dateien ---
@app.route('/killer_wishes/<path:path>')
def serve_killer_wishes(path):
    return send_from_directory(get_path('killer_wishes'), path)

@app.route('/subathon_overlay/<path:path>')
def serve_subathon_overlay(path):
    return send_from_directory(get_path('subathon_overlay'), path)

# KORRIGIERTE ROUTE FÜR DEN TIMER
@app.route('/timer_overlay/<path:path>')
def serve_timer_overlay(path):
    return send_from_directory(get_path('timer_overlay'), path)

# --- App starten ---
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)