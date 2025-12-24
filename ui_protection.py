"""
Mô-đun bảo vệ giao diện, ngăn chặn việc thay đổi giao diện
khi không được phép
"""

import os
import json
import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32process
import time
import sys

# Đường dẫn đến tệp cấu hình
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mt_login_config.json")

# Cấu hình mặc định
DEFAULT_CONFIG = {
    "allow_ui_changes": False,  # Mặc định không cho phép thay đổi giao diện
    "protected_windows": [],    # Danh sách các cửa sổ được bảo vệ (tiêu đề)
    "speed_settings": {
        "focus_delay": 0.5,      # Thời gian chờ sau khi focus cửa sổ (giây)
        "key_delay": 0.1,        # Thời gian chờ giữa các phím (giây)
        "form_open_delay": 1.0,  # Thời gian chờ form đăng nhập mở (giây)
        "field_delay": 0.2       # Thời gian chờ giữa các trường (giây)
    }
}

def load_config():
    """Tải cấu hình từ tệp, tạo mới nếu không tồn tại"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        else:
            # Tạo tệp cấu hình mặc định
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"⚠️ Lỗi khi tải cấu hình: {str(e)}")
        return DEFAULT_CONFIG

def save_config(config):
    """Lưu cấu hình vào tệp"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("✅ Đã lưu cấu hình thành công")
        return True
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu cấu hình: {str(e)}")
        return False

def is_ui_change_allowed():
    """Kiểm tra xem có cho phép thay đổi giao diện không"""
    config = load_config()
    return config.get("allow_ui_changes", False)

def set_ui_change_permission(allowed):
    """Thiết lập quyền thay đổi giao diện"""
    config = load_config()
    config["allow_ui_changes"] = allowed
    return save_config(config)

def protect_window(window_title):
    """Thêm một cửa sổ vào danh sách bảo vệ"""
    config = load_config()
    if window_title not in config.get("protected_windows", []):
        if "protected_windows" not in config:
            config["protected_windows"] = []
        config["protected_windows"].append(window_title)
        return save_config(config)
    return True

def unprotect_window(window_title):
    """Loại bỏ một cửa sổ khỏi danh sách bảo vệ"""
    config = load_config()
    if "protected_windows" in config and window_title in config["protected_windows"]:
        config["protected_windows"].remove(window_title)
        return save_config(config)
    return True

def get_protected_windows():
    """Lấy danh sách các cửa sổ được bảo vệ"""
    config = load_config()
    return config.get("protected_windows", [])

def find_metatrader_windows():
    """Tìm tất cả các cửa sổ MT4/MT5 đang chạy"""
    metatrader_windows = []
    
    def enum_windows_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and ("MetaTrader" in title or "MT4" in title or "MT5" in title):
                results.append({"hwnd": hwnd, "title": title})
    
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    return windows

class UIProtection:
    """Lớp bảo vệ giao diện, ngăn chặn việc thay đổi giao diện"""
    
    def __init__(self):
        self.protected = False
        self.config = load_config()
        self.protected_windows = []
        
    def start_protection(self):
        """Bắt đầu bảo vệ giao diện"""
        if not is_ui_change_allowed():
            self.protected = True
            self.protected_windows = get_protected_windows()
            # Nếu không có cửa sổ nào được bảo vệ, tự động tìm và bảo vệ tất cả cửa sổ MT4/MT5
            if not self.protected_windows:
                windows = find_metatrader_windows()
                for window in windows:
                    protect_window(window["title"])
                self.protected_windows = get_protected_windows()
            
            print(f"✅ Đã bật chế độ bảo vệ giao diện cho {len(self.protected_windows)} cửa sổ")
            return True
        return False
    
    def stop_protection(self):
        """Dừng bảo vệ giao diện"""
        self.protected = False
        print("✅ Đã tắt chế độ bảo vệ giao diện")
        return True
    
    def is_protected(self):
        """Kiểm tra xem có đang bảo vệ không"""
        return self.protected

# Hàm kiểm tra và ngăn chặn thay đổi giao diện
def check_and_block_ui_changes():
    """Kiểm tra và ngăn chặn thay đổi giao diện nếu không được phép"""
    if not is_ui_change_allowed():
        for window in find_metatrader_windows():
            if window["title"] in get_protected_windows():
                hwnd = window["hwnd"]
                # Ngăn chặn thanh cuộn và thay đổi kích thước
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                if style & win32con.WS_THICKFRAME:
                    new_style = style & ~win32con.WS_THICKFRAME
                    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
                    print(f"🔒 Đã khóa thay đổi kích thước cho cửa sổ: {window['title']}")
                
                # Ngăn chặn di chuyển cửa sổ
                new_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                if not (new_style & win32con.WS_EX_TOOLWINDOW):
                    new_style = new_style | win32con.WS_EX_TOOLWINDOW
                    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)
                    print(f"🔒 Đã khóa di chuyển cho cửa sổ: {window['title']}")

def monitor_ui_changes():
    """Giám sát và ngăn chặn thay đổi giao diện"""
    print("Bắt đầu giám sát thay đổi giao diện...")
    
    while True:
        try:
            check_and_block_ui_changes()
            time.sleep(2)  # Kiểm tra mỗi 2 giây
        except KeyboardInterrupt:
            print("Dừng giám sát thay đổi giao diện.")
            break
        except Exception as e:
            print(f"Lỗi khi giám sát: {str(e)}")
            time.sleep(5)  # Nếu gặp lỗi, đợi lâu hơn trước khi thử lại

if __name__ == "__main__":
    # Nếu chạy trực tiếp tệp này, bắt đầu giám sát
    if len(sys.argv) > 1:
        if sys.argv[1] == "--allow":
            set_ui_change_permission(True)
            print("✅ Đã cho phép thay đổi giao diện")
        elif sys.argv[1] == "--disallow":
            set_ui_change_permission(False)
            print("✅ Đã cấm thay đổi giao diện")
        elif sys.argv[1] == "--protect":
            if len(sys.argv) > 2:
                protect_window(sys.argv[2])
                print(f"✅ Đã thêm cửa sổ '{sys.argv[2]}' vào danh sách bảo vệ")
            else:
                windows = find_metatrader_windows()
                for window in windows:
                    protect_window(window["title"])
                print(f"✅ Đã bảo vệ {len(windows)} cửa sổ")
        elif sys.argv[1] == "--unprotect":
            if len(sys.argv) > 2:
                unprotect_window(sys.argv[2])
                print(f"✅ Đã loại bỏ cửa sổ '{sys.argv[2]}' khỏi danh sách bảo vệ")
            else:
                config = load_config()
                config["protected_windows"] = []
                save_config(config)
                print("✅ Đã xóa tất cả cửa sổ khỏi danh sách bảo vệ")
        elif sys.argv[1] == "--list":
            protected_windows = get_protected_windows()
            print(f"Danh sách {len(protected_windows)} cửa sổ được bảo vệ:")
            for window in protected_windows:
                print(f"- {window}")
    else:
        # Bắt đầu giám sát
        monitor_ui_changes() 