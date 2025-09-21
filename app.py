from flask import Flask, jsonify, send_from_directory, request
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

# Konfiguration des Loggers für diese Datei
wishes_logger = logging.getLogger('wishes_logger')
wishes_logger.setLevel(logging.INFO)
wishes_handler = logging.FileHandler(get_path('wishes.log'))
wishes_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
wishes_logger.addHandler(wishes_handler)

# Wichtige Änderung: Datenbankpfad
DATABASE = get_path('killerwuensche.db')
offset_counter = 0


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# API-Endpunkt für die Anzeige von 2 Wünschen mit Offset
@app.route('/killer_wishes/data', methods=['GET'])
def get_killer_wishes_data():
    global offset_counter
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT wunsch, user_name FROM killer_wuensche ORDER BY datum DESC LIMIT 2 OFFSET ?", (offset_counter,))
    wuensche = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(wuensche)


# API-Endpunkt für den Hotkey, um den nächsten Wunsch anzuzeigen
@app.route('/killer_wishes/next', methods=['POST'])
def next_killer():
    global offset_counter
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM killer_wuensche")
    total_wishes = c.fetchone()[0]
    conn.close()

    offset_counter += 2
    if offset_counter >= total_wishes:
        offset_counter = 0

    return jsonify({'message': 'Offset aktualisiert', 'new_offset': offset_counter})


# API-Endpunkt zum Zurücksetzen der Datenbank
@app.route('/killer_wishes/reset', methods=['POST'])
def reset_database():
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM killer_wuensche")
    conn.commit()
    conn.close()
    return jsonify({'message': 'Datenbank erfolgreich zurückgesetzt.'}), 200


# API-Endpunkt zum Hinzufügen von Wünschen
@app.route('/killerwuensche', methods=['POST'])
def add_killerwunsch():
    if not request.json or 'wunsch' not in request.json or 'user_name' not in request.json:
        wishes_logger.error('Fehler: Falsches Format beim Hinzufügen eines Wunsches.')
        return jsonify({'error': 'Falsches Format, "wunsch" oder "user_name" fehlt.'}), 400

    wunsch = request.json['wunsch']
    user_name = request.json['user_name']

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO killer_wuensche (wunsch, user_name) VALUES (?, ?)", (wunsch, user_name))
        conn.commit()
        conn.close()
        wishes_logger.info(f'Neuer Wunsch hinzugefügt von {user_name}: {wunsch}')
        return jsonify({'message': 'Wunsch erfolgreich hinzugefügt.'}), 201
    except Exception as e:
        wishes_logger.error(f'Datenbank-Fehler beim Hinzufügen des Wunsches: {e}')
        return jsonify({'error': 'Fehler beim Hinzufügen des Wunsches.'}), 500


# Statische Dateien für Killer-Wünsche
@app.route('/killer_wishes/<path:path>')
def serve_killer_wishes(path):
    directory = get_path('killer_wishes')
    return send_from_directory(directory, path)



# Statische Dateien für Subathon-Overlay
@app.route('/subathon_overlay/<path:path>')
def serve_subathon_overlay(path):
    directory = get_path('subathon_overlay')
    return send_from_directory(directory, path)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
