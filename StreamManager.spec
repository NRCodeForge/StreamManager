# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('pynput')

datas = [
    ('killerwuensche.db', '.'),
    ('killer_wishes/*', 'killer_wishes'),
    ('subathon_overlay/*', 'subathon_overlay')
]

# --- WEBSERVER ---
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
    noarchive=False,
)
pyz_web = PYZ(a_web.pure, a_web.zipped_data, cipher=None)
webserver_exe = EXE(
    pyz_web,
    a_web.scripts,
    [],
    exclude_binaries=True,
    name='webserver',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)

# --- STREAMMANAGER ---
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
    noarchive=False,
)
pyz_gui = PYZ(a_gui.pure, a_gui.zipped_data, cipher=None)
streammanager_exe = EXE(
    pyz_gui,
    a_gui.scripts,
    [],
    exclude_binaries=True,
    name='StreamManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    windowed=True
)

# --- beide in einen Ordner (gemeinsames COLLECT) ---
coll = COLLECT(
    [webserver_exe, streammanager_exe],
    a_web.binaries + a_gui.binaries,
    a_web.zipfiles + a_gui.zipfiles,
    a_web.datas + a_gui.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StreamBundle'
)
