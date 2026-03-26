# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['core/main.py'],
    pathex=['/home/ewerton/speedscan/speedscan'],
    binaries=[],
    datas=[('locale', 'locale'), ('assets', 'assets')],
    hiddenimports=['core', 'core.actions', 'core.ui', 'core.config', 'core.hardware', 'core.health_score', 'core.temperature_monitor', 'core.smart_monitor', 'core.browser_cleaner', 'core.speed_test', 'core.process_manager', 'core.historical_metrics', 'core.lan_scanner', 'core.ai_proactive', 'core.security_scanner', 'core.lan_cache', 'core.chat', 'core.first_run', 'core.cookie_manager', 'core.trash_manager', 'core.windows_cleaner', 'core.scheduler', 'core.i18n', 'core.dashboard', 'tkinter', 'customtkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SpeedScan-Linux',
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
    icon=None
)
