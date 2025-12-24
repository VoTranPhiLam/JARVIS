# -*- mode: python ; coding: utf-8 -*-

import sys
from os import path

block_cipher = None

# Danh sách các hook cần thêm vào
added_hooks = [
    'hook-psutil.py',
    'hook-pythoncom.py',
    'hook-pywinauto.py',
    'hook-win32com.py'
]

# Danh sách các module bổ sung cần thêm vào
added_modules = []

# Thêm các module cần thiết từ các file hook
for hook in added_hooks:
    if path.exists(hook):
        with open(hook, 'r') as f:
            for line in f:
                if 'hiddenimports' in line and '=' in line:
                    modules = line.split('=')[1].strip()
                    modules = modules.strip('[]').replace("'", "").replace('"', '')
                    for module in modules.split(','):
                        module = module.strip()
                        if module and module not in added_modules:
                            added_modules.append(module)

a = Analysis(
    ['mt_login_sheets.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('credentials.json', '.'),
        ('config.json', '.'),
        ('mt_login_config.json', '.')
    ],
    hiddenimports=added_modules + [
        'win32api', 'win32con', 'win32gui', 'win32process',
        'win32com', 'win32com.client', 'pythoncom',
        'psutil', 'pandas', 'gspread', 'oauth2client',
        'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
        'pyautogui', 'pyperclip'
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
    name='MT4_MT5_Login',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
