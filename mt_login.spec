# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect all necessary modules and their dependencies
pywin32_modules = collect_submodules('win32com')
pythoncom_modules = collect_submodules('pythoncom')
pywinauto_modules = collect_submodules('pywinauto')
psutil_modules = collect_submodules('psutil')

# Collect data files safely
pywin32_data = collect_data_files('win32com')

a = Analysis(
    ['mt_login_sheets.py'],
    pathex=[r'D:\\Ung Dung Dang Nhap TK'],
    binaries=[],
    datas=[
        ('credentials.json', '.'), 
        ('config.json', '.'),
    ],
    hiddenimports=[
        'gspread', 
        'oauth2client',
        'pandas',
        'pyperclip',
        'win32api',
        'win32con',
        'win32gui',
        'win32process',
        'win32security',
        'win32event',
        'win32timezone',
        'win32com.client',
        'win32com.shell',
        'pythoncom',
        'pywintypes',
        'comtypes',
        'pywinauto',
        'pywinauto.application',
        'pywinauto.findwindows',
        'pywinauto.controls.win32_controls',
        'pywinauto.controls.common_controls',
        'pywinauto.keyboard',
        'pywinauto.mouse',
        'pywinauto.windows',
        'pywinauto.base_wrapper',
        'pyautogui',
        'pyautogui._pyautogui_win',
        'psutil',
        'psutil._pswindows',
        'psutil._psutil_windows',
        # Thêm các module khác cần thiết
        'ctypes',
        'PIL',
        'PIL._tkinter_finder',
        'PIL._version',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ] + pywin32_modules + pythoncom_modules + pywinauto_modules + psutil_modules,
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Thêm các DLL của psutil
import psutil
psutil_dir = os.path.dirname(psutil.__file__)
for filename in os.listdir(psutil_dir):
    if filename.endswith('.dll'):
        a.binaries.append(('psutil/' + filename, os.path.join(psutil_dir, filename), 'BINARY'))

# Thêm các DLL khác mà có thể cần thiết (comtypes, pywin32, etc.)
try:
    import comtypes
    comtypes_dir = os.path.dirname(comtypes.__file__)
    for filename in os.listdir(comtypes_dir):
        if filename.endswith('.dll'):
            a.binaries.append(('comtypes/' + filename, os.path.join(comtypes_dir, filename), 'BINARY'))
except ImportError:
    pass

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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
