# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['exam_system.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('backups', 'backups'),
        ('database', 'database')
    ],
    hiddenimports=[
        'babel.numbers',
        'tkinter',
        'sqlite3',
        'pandas',
        'openpyxl'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='نظام توزيع المراقبين',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)