# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules

# --- Konfiguration ---
# Versteckte Importe, die PyInstaller übersehen könnte (pynput ist hier ein gutes Beispiel)
hiddenimports = collect_submodules('pynput')

# Datendateien, die ins finale Programmverzeichnis kopiert werden müssen.
# HINWEIS: Python-Dateien (.py) gehören hier NICHT hinein!
datas = [
    ('killerwuensche.db', '.'),          # Deine Datenbank
    ('killer_wishes', 'killer_wishes'),  # Der Ordner für das Web-Overlay
    ('subathon_overlay', 'subathon_overlay'), # Der Ordner für das Subathon-Overlay
    ('timer_overlay', 'timer_overlay')   # Der Ordner für das Timer-Overlay
]

# --- Build-Prozess für den Webserver (app.py) ---
a_web = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)
pyz_web = PYZ(a_web.pure)
webserver_exe = EXE(
    pyz_web,
    a_web.scripts,
    name='webserver',
    debug=False,
    strip=False,
    upx=True,
    console=True, # Webserver läuft in einer Konsole (im Hintergrund)
    icon=None
)

# --- Build-Prozess für die GUI (gui.py) ---
a_gui = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)
pyz_gui = PYZ(a_gui.pure)
streammanager_exe = EXE(
    pyz_gui,
    a_gui.scripts,
    name='StreamManager_V.1.1',
    debug=False,
    strip=False,
    upx=True,
    console=False, # GUI ist eine Fensteranwendung
    windowed=True,
    icon=None # Optional: 'pfad/zu/deinem/icon.ico'
)

# --- Alles zu einem finalen Ordner zusammenfügen ---
coll = COLLECT(
    webserver_exe,
    streammanager_exe,
    a_web.binaries,
    a_web.zipfiles,
    a_web.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StreamBundle' # Name des finalen Ausgabeordners
)