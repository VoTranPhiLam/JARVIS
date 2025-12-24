import pyperclip
from pywinauto import Desktop, Application
import pyautogui
import time
import re
import os
import json
import psutil

# Config để lưu trữ các tùy chỉnh
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mt_login_config.json")

# Mặc định config
DEFAULT_CONFIG = {
    "allow_ui_changes": False,  # Mặc định không cho phép thay đổi giao diện
    "speed_settings": {
        "focus_delay": 0.5,      # Thời gian chờ sau khi focus cửa sổ (giây)
        "key_delay": 0.1,        # Thời gian chờ giữa các phím (giây)
        "form_open_delay": 1.0,  # Thời gian chờ form đăng nhập mở (giây)
        "field_delay": 0.2       # Thời gian chờ giữa các trường (giây)
    }
}

def load_config():
    """Tải config từ file, tạo mới nếu không tồn tại"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        else:
            # Tạo file config mặc định
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"⚠️ Lỗi khi tải config: {str(e)}")
        return DEFAULT_CONFIG

def save_config(config):
    """Lưu config vào file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("✅ Đã lưu cấu hình thành công")
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu config: {str(e)}")

def clear_clipboard():
    pyperclip.copy('')

def detect_platform_type(window_obj):
    """Xác định loại nền tảng (MT4 hoặc MT5) dựa vào quy trình thực thi và tiêu đề cửa sổ
    
    MT4 sử dụng: terminal.exe
    MT5 sử dụng: terminal64.exe
    """
    try:
        # Lấy process ID của cửa sổ
        process_id = None
        try:
            process_id = window_obj.process_id()
        except Exception as e:
            print(f"Không thể lấy process_id: {str(e)}")
            return "MT4"  # Mặc định là MT4 nếu không lấy được process ID
        
        # Sử dụng danh sách process hiện tại để xác định
        try:
            all_processes = {proc.pid: proc.name() for proc in psutil.process_iter(['pid', 'name'])}
            
            # Lấy tên process dựa vào process_id
            if process_id in all_processes:
                process_name = all_processes[process_id].lower()
                
                # Kiểm tra tên process
                if "terminal64" in process_name:
                    print(f"Phát hiện MT5 từ tên process: {process_name}")
                    return "MT5"
                elif "terminal" in process_name and "64" not in process_name:
                    print(f"Phát hiện MT4 từ tên process: {process_name}")
                    return "MT4"
        except Exception as process_err:
            print(f"Lỗi khi xác định qua process: {str(process_err)}")
        
        # Nếu không xác định được qua process, thử thông qua tên cửa sổ
        window_title = window_obj.window_text()
        
        # Kiểm tra tên cửa sổ
        title_lower = window_title.lower()
        if "mt5" in title_lower or "metatrader 5" in title_lower:
            print(f"Phát hiện MT5 từ tiêu đề: {window_title}")
            return "MT5"
        elif "mt4" in title_lower or "metatrader 4" in title_lower:
            print(f"Phát hiện MT4 từ tiêu đề: {window_title}")
            return "MT4"
        
        # Phân tích thêm từ tiêu đề
        if "5." in title_lower and "meta" in title_lower:
            print(f"Phát hiện MT5 từ phiên bản: {window_title}")
            return "MT5"
        elif "4." in title_lower and "meta" in title_lower:
            print(f"Phát hiện MT4 từ phiên bản: {window_title}")
            return "MT4"
            
        # Mặc định là MT4
        print(f"Không xác định được, mặc định là MT4: {window_title}")
        return "MT4"
        
    except Exception as e:
        print(f"Lỗi khi xác định loại nền tảng: {str(e)}")
        return "MT4"  # Mặc định là MT4 nếu xảy ra lỗi

def get_all_running_mt_terminals():
    """Tìm tất cả các cửa sổ MT4/MT5 đang chạy và xác định nền tảng"""
    windows = Desktop(backend="win32").windows()
    mt_terminals = []
    
    print("🧭 Đang tìm tất cả các cửa sổ MT4/MT5 đang chạy:")
    for win in windows:
        try:
            title = win.window_text()
            if not title:
                continue
                
            title_lower = title.lower()
            mt_keywords = ["metatrader", "mt4", "mt5"]
            
            # Chỉ xem xét các cửa sổ MetaTrader
            if any(keyword in title_lower for keyword in mt_keywords):
                platform_type = detect_platform_type(win)
                mt_terminals.append({
                    "window": win,
                    "title": title,
                    "platform": platform_type
                })
                print(f"- {title} ({platform_type})")
        except Exception as e:
            print(f"- Lỗi khi xử lý cửa sổ: {str(e)}")
    
    return mt_terminals

def check_platform_compatibility(mt_terminals, target_platform_type):
    """Kiểm tra xem nền tảng đích có tương thích với các cửa sổ MT đang chạy không"""
    if not mt_terminals:
        print("✅ Không tìm thấy cửa sổ MT nào đang chạy, có thể đăng nhập bất kỳ nền tảng nào")
        return True, ""
    
    # Lấy nền tảng của các cửa sổ đang chạy
    running_platforms = set([terminal["platform"] for terminal in mt_terminals])
    
    # Nếu chỉ có một loại nền tảng đang chạy
    if len(running_platforms) == 1:
        running_platform = list(running_platforms)[0]
        if running_platform != target_platform_type:
            error_msg = f"⚠️ Không thể đăng nhập tài khoản {target_platform_type} khi đang có {running_platform} đang chạy"
            print(error_msg)
            return False, error_msg
    
    # Nếu có nhiều loại nền tảng đang chạy, cho phép đăng nhập
    return True, ""

def standardize_server_name(server):
    """Chuẩn hóa tên server dựa trên các pattern phổ biến"""
    server = server.strip()
    
    # Danh sách các prefix cần loại bỏ
    prefixes_to_remove = ['STD_', 'MT4', 'MT5', 'Trade', 'TradeMT4-', 'TradeMT5-']
    
    # Dictionary ánh xạ tên server
    server_mappings = {
        'SkillingLimited': ['STD_SkillingLimited', 'Skilling-Live', 'Skilling'],
        'AdmiralsSC-Live': ['TradeMT5-AdmiralsSC-Live', 'AdmiralMarkets', 'Admirals'],
        # Thêm các mapping khác ở đây
    }
    
    # Kiểm tra trong server_mappings
    for standard_name, variants in server_mappings.items():
        if any(variant.lower() in server.lower() for variant in variants):
            print(f"🔄 Chuẩn hóa server từ '{server}' thành '{standard_name}'")
            return standard_name
    
    # Nếu không có trong mappings, thử loại bỏ các prefix
    original_server = server
    for prefix in prefixes_to_remove:
        if server.startswith(prefix):
            server = server[len(prefix):]
            print(f"🔄 Loại bỏ prefix '{prefix}' từ tên server")
            break
    
    if original_server != server:
        print(f"🔄 Chuẩn hóa server từ '{original_server}' thành '{server}'")
    
    return server

def is_likely_password(text):
    """Kiểm tra xem một chuỗi có phải là password không"""
    # Password là chuỗi liên tục không có khoảng trắng
    if ' ' in text:
        return False
    
    # Không phải là số thuần túy
    if text.isdigit():
        return False
    
    # Không phải là các từ khóa phổ biến
    keywords = ['login', 'pass', 'server', 'account', 'mt4', 'mt5', 'live', 'demo']
    if text.lower() in keywords:
        return False
        
    return True

def parse_account_info(text):
    """Phân tích và trích xuất thông tin tài khoản từ nhiều định dạng khác nhau"""
    text = text.strip()
    
    print("\n📋 THÔNG TIN CLIPBOARD GỐC:")
    print("------------------------")
    print(text)
    print("------------------------")
    
    # Xóa các ký tự đặc biệt và chuẩn hóa khoảng trắng
    text = re.sub(r'\s+', ' ', text)
    parts = text.split()
    
    print("\n🔍 PHÂN TÍCH TỪNG PHẦN:")
    print("------------------------")
    print(f"Các phần tách được: {parts}")
    
    result = {}
    
    # Tìm login ID (số có 4 chữ số trở lên)
    for part in parts:
        if re.match(r'^\d{4,}$', part):
            result['login'] = part
            print(f"✅ Tìm thấy Login ID: {part} (số có {len(part)} chữ số)")
            break
    
    if 'login' not in result:
        # Thử tìm số trong các phần có chứa từ khóa
        for part in parts:
            numbers = re.findall(r'\d{4,}', part)
            if numbers:
                result['login'] = numbers[0]
                print(f"✅ Tìm thấy Login ID trong phần: {part} -> {numbers[0]}")
                break
    
    # Tìm password (chuỗi liên tục không có khoảng trắng)
    potential_passwords = []
    for part in parts:
        if is_likely_password(part):
            potential_passwords.append(part)
            print(f"💡 Password tiềm năng: {part}")
    
    if potential_passwords:
        # Ưu tiên password ở cuối chuỗi
        result['password'] = potential_passwords[-1]
        print(f"✅ Chọn Password: {result['password']}")
    
    # Server là phần đầu tiên
    result['server'] = parts[0]
    print(f"✅ Server: {result['server']}")
    
    # Broker là phần thứ hai hoặc tìm trong text
    if len(parts) > 1:
        result['broker'] = parts[1]
    else:
        result['broker'] = "unknown"
    print(f"✅ Broker: {result['broker']}")

    # Xác định nền tảng dựa vào tên server hoặc các thông tin khác
    if "MT5" in text or "mt5" in text.lower() or "metatrader 5" in text.lower():
        result['platform'] = "MT5"
    else:
        result['platform'] = "MT4"  # Mặc định là MT4 nếu không có dấu hiệu rõ ràng là MT5
    print(f"✅ Nền tảng: {result['platform']}")
    
    if 'login' in result and 'password' in result:
        return result
    
    raise ValueError("⚠️ Không thể nhận diện được định dạng tài khoản!")

def extract_broker(text):
    """Trích xuất tên broker từ text"""
    # Danh sách các broker phổ biến
    common_brokers = {
        'tradingpro': ['tradingpro', 'trading pro', 'trading-pro'],
        'skilling': ['skilling', 'skillinglimited'],
        'admirals': ['admirals', 'admiralsc', 'admiral'],
        'exness': ['exness'],
        'fbs': ['fbs'],
        'xm': ['xm'],
        'fxtm': ['fxtm'],
        'forex4you': ['forex4you']
    }
    
    text = text.lower()
    # Tìm broker trong danh sách phổ biến
    for broker, variants in common_brokers.items():
        if any(variant in text for variant in variants):
            return broker
    
    # Nếu không tìm thấy broker phổ biến, tìm từ có độ dài > 3 không phải là các từ khóa
    words = text.split()
    keywords = ['login', 'pass', 'server', 'account', 'password', 'id', 'tài', 'khoản', 'mật', 'khẩu', 'máy', 'chủ', 'mt4', 'mt5', 'live', 'demo', 'limited', 'trading']
    
    for word in words:
        if len(word) > 3 and word.lower() not in keywords and not re.match(r'^\d+$', word):
            return word
    
    return "unknown"

try:
    # Tải config
    config = load_config()
    speed_settings = config.get("speed_settings", DEFAULT_CONFIG["speed_settings"])
    
    # ====== BƯỚC 1: LẤY VÀ PHÂN TÍCH THÔNG TIN ======
    raw = pyperclip.paste().strip()
    if not raw:
        raise ValueError("⚠️ Clipboard trống! Vui lòng copy thông tin tài khoản trước.")
    
    # Phân tích thông tin
    account_info = parse_account_info(raw)
    
    server_name = account_info['server']
    broker_keyword = account_info['broker']
    login_id = account_info['login']
    password = account_info['password']
    platform_type = account_info['platform']

    print("\n📋 KẾT QUẢ CUỐI CÙNG:")
    print("------------------------")
    print(f"🔹 Server: {server_name}")
    print(f"🔹 Broker: {broker_keyword}")
    print(f"🔹 Login ID: {login_id}")
    print(f"🔹 Password: {password}")
    print(f"🔹 Nền tảng: {platform_type}")
    print("------------------------")
    
    # ====== BƯỚC 1.5: KIỂM TRA TÍNH TƯƠNG THÍCH PLATFORM ======
    print("\n🔍 ĐANG KIỂM TRA TÍNH TƯƠNG THÍCH NỀN TẢNG:")
    print("------------------------")
    mt_terminals = get_all_running_mt_terminals()
    compatible, error_message = check_platform_compatibility(mt_terminals, platform_type)
    
    if not compatible:
        print(error_message)
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Ẩn cửa sổ chính
        messagebox.showerror("Lỗi Tương Thích Nền Tảng", error_message)
        root.destroy()
        raise ValueError(error_message)
    else:
        print("✅ Nền tảng tương thích, tiếp tục đăng nhập")
    print("------------------------")
    
    confirm = input("\n❓ Thông tin đã đúng chưa? (Y/N): ").strip().lower()
    if confirm != 'y':
        raise ValueError("⚠️ Người dùng đã hủy thao tác!")
    print()

    # Xóa thông tin nhạy cảm khỏi clipboard
    clear_clipboard()

    print(f"🔍 Đang tìm cửa sổ MT4/5 có chứa tên sàn: {broker_keyword}")

    # ====== BƯỚC 2: TÌM CỬA SỔ MT4/5 ======
    windows = Desktop(backend="win32").windows()
    target_win = None

    print("🧭 Danh sách cửa sổ đang mở:")
    for win in windows:
        title = win.window_text()
        print("-", title)
        if broker_keyword.lower() in title.lower():
            target_win = win
            break

    if not target_win:
        raise Exception(f"❌ Không tìm thấy cửa sổ chứa: {broker_keyword}")

    print("✅ Đã tìm thấy cửa sổ:", target_win.window_text())

    # ====== BƯỚC 3: GỌI LOGIN (Alt+F → L) ======
    app = Application(backend="win32").connect(handle=target_win.handle)
    main_win = app.window(handle=target_win.handle)
    main_win.set_focus()
    time.sleep(speed_settings["focus_delay"])  # Giảm thời gian chờ sau khi focus

    # Mở form login
    pyautogui.hotkey('alt', 'f')
    time.sleep(speed_settings["key_delay"])
    pyautogui.press('l')
    time.sleep(speed_settings["form_open_delay"])  # Đợi form login hiện lên

    print("✅ Đã mở form Login")

    # ====== BƯỚC 4: ĐIỀN THÔNG TIN LOGIN ======
    try:
        print("\n🔄 ĐANG ĐIỀN FORM LOGIN:")
        print("------------------------")
        
        # Điền Login ID (form tự focus vào trường ID)
        print("➡️ Điền Login ID...")
        pyperclip.copy(login_id)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(speed_settings["field_delay"])
        pyautogui.press('tab')
        time.sleep(speed_settings["field_delay"])
        
        # Điền Password
        print("➡️ Điền Password...")
        pyperclip.copy(password)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(speed_settings["field_delay"])
        pyautogui.press('tab')
        time.sleep(speed_settings["field_delay"])
        
        # Điền Server name
        print("➡️ Điền Server...")
        pyperclip.copy(server_name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(speed_settings["field_delay"])
        
        # Tab 2 lần để focus vào nút OK
        print("➡️ Di chuyển đến nút OK...")
        pyautogui.press('tab')
        time.sleep(speed_settings["key_delay"])
        pyautogui.press('tab')
        time.sleep(speed_settings["key_delay"])

        # Nhấn Enter để submit
        print("➡️ Nhấn Enter để đăng nhập...")
        pyautogui.press('enter')
        print("------------------------")
        print(f"🚀 Đã gửi yêu cầu đăng nhập tài khoản: {login_id}")

        # Xóa các biến nhạy cảm
        del login_id, password, raw, account_info

    except Exception as e:
        print(f"❌ Lỗi khi điền form: {str(e)}")
        raise

finally:
    # Đảm bảo xóa thông tin nhạy cảm
    clear_clipboard()
