# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('wiper_core.dll', '.'), ('icon.ico', '.'), ('certificate.py', '.'), ('disk_manager.py', '.'), ('wiper.py', '.'), ('scalpel.conf', '.'), ('forensic_cases.json', '.'), ('core', 'core'), ('engines', 'engines'), ('ui', 'ui')],
    hiddenimports=['pypdf', 'PIL', 'wmi', 'customtkinter', 'fpdf'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ZeroTrace',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
