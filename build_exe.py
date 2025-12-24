import os
import sys
import shutil
import subprocess
import json
import platform

def build_standalone_exe():
    print("======== BẮT ĐẦU ĐÓNG GÓI ỨNG DỤNG THÀNH FILE EXE ========")
    
    # Tạo thư mục build và dist nếu chưa có
    for folder in ['build', 'dist']:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # Tạo hoặc cập nhật file spec
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

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
"""
    
    # Lưu file spec
    with open('MT4_MT5_Login.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # Tạo các hook file nếu chưa có
    hooks = {
        'hook-psutil.py': "# Hook for psutil\nhiddenimports = ['psutil._pswindows']",
        'hook-pythoncom.py': "# Hook for pythoncom\nhiddenimports = ['pythoncom']",
        'hook-pywinauto.py': "# Hook for pywinauto\nhiddenimports = ['pywinauto.timings', 'pywinauto.findwindows', 'pywinauto.controls']",
        'hook-win32com.py': "# Hook for win32com\nhiddenimports = ['win32com.client', 'win32com.server', 'win32com.gen_py']"
    }
    
    for hook_file, content in hooks.items():
        if not os.path.exists(hook_file):
            with open(hook_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Đã tạo file hook: {hook_file}")
    
    # Tạo file config mẫu nếu chưa có
    if not os.path.exists('config.json'):
        config = {
            "sheet_url": "",
            "worksheet": "Sheet1",
            "header_row": "1",
            "broker_col": "F",
            "server_col": "D",
            "login_col": "G",
            "pass_col": "I"
        }
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("Đã tạo file config.json mẫu")
    
    # Tạo file cấu hình tốc độ mẫu nếu chưa có
    if not os.path.exists('mt_login_config.json'):
        speed_config = {
            "speed_settings": {
                "focus_delay": 0.5,
                "key_delay": 0.1,
                "form_open_delay": 1.0,
                "field_delay": 0.2
            }
        }
        with open('mt_login_config.json', 'w', encoding='utf-8') as f:
            json.dump(speed_config, f, indent=4, ensure_ascii=False)
        print("Đã tạo file mt_login_config.json mẫu")
    
    # Kiểm tra credentials
    if not os.path.exists('credentials.json'):
        print("CẢNH BÁO: Không tìm thấy file credentials.json, bạn cần thêm file này để kết nối với Google Sheets")
    
    # Cài đặt các package cần thiết
    print("Đang cài đặt các package cần thiết...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Biên dịch ứng dụng
    print("\nĐang biên dịch ứng dụng thành file EXE...")
    subprocess.run(["pyinstaller", "MT4_MT5_Login.spec"])
    
    # Tạo file run.bat trong thư mục dist
    run_bat = """@echo off
echo Đang khởi động ứng dụng MT4_MT5_Login...
start MT4_MT5_Login.exe
"""
    with open('dist/run.bat', 'w', encoding='utf-8') as f:
        f.write(run_bat)
    
    # Tạo README cho file exe
    readme = """# HƯỚNG DẪN SỬ DỤNG ỨNG DỤNG MT4_MT5_LOGIN

## Chuẩn bị
1. Đảm bảo file credentials.json có trong thư mục cùng với file EXE (nếu chưa có, hãy sao chép từ thư mục gốc)
2. Cấu hình file config.json theo nhu cầu của bạn (URL Google Sheet, cột dữ liệu)

## Khởi động ứng dụng
1. Double-click vào file MT4_MT5_Login.exe
2. Hoặc chạy file run.bat

## Tính năng chính
- Kết nối và lấy dữ liệu từ Google Sheets
- Kiểm tra tài khoản đúng nhánh
- Hỗ trợ đăng nhập nhiều tài khoản MT4/MT5 cùng lúc
- Tìm kiếm tài khoản thay thế phù hợp

## Lưu ý
- Đảm bảo MT4/MT5 đã được mở trước khi sử dụng chức năng đăng nhập
- Có thể điều chỉnh tốc độ đăng nhập trong file mt_login_config.json
"""
    with open('dist/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme)
    
    # Sao chép các file cần thiết vào thư mục dist
    necessary_files = ['credentials.json', 'config.json', 'mt_login_config.json']
    for file in necessary_files:
        if os.path.exists(file):
            # Chỉ copy nếu file chưa tồn tại trong dist
            if not os.path.exists(f'dist/{file}'):
                shutil.copy2(file, f'dist/{file}')
                print(f"Đã sao chép {file} vào thư mục dist")
    
    print("\n======== ĐÓNG GÓI HOÀN TẤT ========")
    print("File EXE đã được tạo tại: dist/MT4_MT5_Login.exe")
    print("Bạn có thể chạy file này hoặc file run.bat để khởi động ứng dụng")

if __name__ == "__main__":
    build_standalone_exe() 