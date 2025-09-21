import sqlite3
import os

def setup_database(db_path):
    """
    Erstellt oder aktualisiert die Datenbanktabelle für die Killerwünsche.
    Nimmt den korrekten Pfad zur Datenbank als Argument.
    """
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS killer_wuensche (
                id INTEGER PRIMARY KEY,
                wunsch TEXT NOT NULL,
                user_name TEXT NOT NULL,
                datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("Datenbank und Tabelle erfolgreich erstellt oder aktualisiert.")
    except Exception as e:
        print(f"Fehler beim Einrichten der Datenbank: {e}")

if __name__ == '__main__':
    # Nur zum direkten Testen, im fertigen Programm wird es von gui.py aufgerufen.
    setup_database('killerwuensche.db')