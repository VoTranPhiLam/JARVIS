# 📊 Google Sheets Integration Guide

Hướng dẫn tích hợp Google Sheets vào JARVIS để lấy dữ liệu tài khoản.

---

## 🎯 Tính Năng Mới

Với Google Sheets integration, JARVIS có thể:

1. **Kết nối đến Google Sheets** để lấy dữ liệu tài khoản
2. **Tự động load accounts** từ Sheets khi khởi động
3. **Query thông tin tài khoản** bằng AI chat:
   - "Cho tôi xem thông tin tài khoản Exness"
   - "Tài khoản login 12345678 có server gì?"
   - "Các tài khoản MT5 nào đang có?"
4. **Đăng nhập tự động** sau khi AI tìm thấy thông tin

---

## 📋 Yêu Cầu

### 1. Google Cloud Project Setup

Bạn cần tạo Google Cloud Project và enable Google Sheets API:

**Bước 1: Tạo Project**
1. Truy cập https://console.cloud.google.com/
2. Tạo project mới (hoặc chọn project hiện tại)
3. Nhớ tên project

**Bước 2: Enable Google Sheets API**
1. Trong project, vào **APIs & Services** > **Library**
2. Tìm "Google Sheets API"
3. Click **Enable**

**Bước 3: Tạo Service Account**
1. Vào **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Điền tên (ví dụ: "JARVIS Sheets Reader")
4. Grant role: **Editor** (hoặc tối thiểu **Viewer** nếu chỉ đọc)
5. Click **Done**

**Bước 4: Tạo Key cho Service Account**
1. Click vào Service Account vừa tạo
2. Vào tab **Keys**
3. Click **Add Key** > **Create new key**
4. Chọn **JSON**
5. Download file JSON về

**Bước 5: Rename file**
- Đổi tên file JSON thành `credentials.json`
- Copy file vào thư mục `/home/user/JARVIS/`

### 2. Share Google Sheet với Service Account

**Quan trọng**: Service Account cần quyền truy cập vào Sheet

1. Mở file `credentials.json` vừa download
2. Copy email của service account (dạng: `xxx@xxx.iam.gserviceaccount.com`)
3. Mở Google Sheet bạn muốn sử dụng
4. Click **Share**
5. Paste email service account vào
6. Chọn quyền: **Viewer** (hoặc **Editor** nếu cần write)
7. Click **Send**

---

## 🏗️ Cấu Trúc Google Sheet

### Định Dạng Chuẩn

Google Sheet của bạn nên có các cột sau (tên cột có thể khác nhau):

| Login/ID | Broker | Platform/Type | Server | Password | Name |
|----------|--------|---------------|---------|----------|------|
| 12345678 | Exness | MT5 | Exness-MT5Live | MyPass123 | Exness Main |
| 87654321 | XM | MT4 | XM-Real 3 | Pass456 | XM Demo |

**Lưu ý**:
- Cột **Login/ID**: Bắt buộc - số tài khoản
- Cột **Broker**: Bắt buộc - tên sàn
- Cột **Platform/Type**: MT4 hoặc MT5
- Cột **Server**: Tên server
- Cột **Password**: Mật khẩu (optional nhưng cần cho login)
- Cột **Name**: Tên gợi nhớ (optional)

**Tên cột linh hoạt**:
- Login: "Login", "ID", "Account", "Account ID"
- Broker: "Broker", "Sàn"
- Platform: "Platform", "Type", "Loại"
- Server: "Server", "Máy chủ"
- Password: "Password", "Pass", "Mật khẩu"
- Name: "Name", "Tên"

Hệ thống tự động nhận diện các cột dựa trên từ khóa.

---

## 🔧 Cấu Hình JARVIS

### 1. Update `config/ai_config.json`

Thêm section Google Sheets:

```json
{
  "ai_provider": "mock",

  "google_sheets": {
    "enabled": true,
    "sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit",
    "worksheet_name": "Sheet1",
    "header_row": 1,
    "auto_load_on_startup": true
  },

  "openai": {
    ...
  }
}
```

**Giải thích**:
- `enabled`: Bật/tắt Google Sheets integration
- `sheet_url`: URL đầy đủ của Google Sheet
- `worksheet_name`: Tên worksheet (tab) cần load
- `header_row`: Dòng chứa header (thường là 1)
- `auto_load_on_startup`: Tự động load khi khởi động?

### 2. Đảm Bảo Có `credentials.json`

```bash
ls /home/user/JARVIS/credentials.json
# Phải thấy file này
```

---

## 🚀 Sử Dụng

### Load Accounts Từ Google Sheets

**Cách 1: Tự động khi khởi động**

Nếu `auto_load_on_startup: true` trong config, JARVIS sẽ tự động:
1. Connect đến Google Sheets
2. Load tất cả accounts
3. Merge với accounts local (trong `config/accounts.json`)
4. Sẵn sàng để query

**Cách 2: Manual load qua GUI**

Trong Main Window:
1. Click nút **"Connect to Sheets"** (sẽ được thêm vào GUI)
2. Nhập Sheet URL và Worksheet name (hoặc dùng config)
3. Click **"Load Accounts"**

**Cách 3: Qua code**

```python
from core import AccountManager

# Create manager với Sheets enabled
manager = AccountManager(use_sheets=True)

# Connect to sheet
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
manager.connect_sheets(sheet_url, "Sheet1")

# Load accounts
manager.load_from_sheets(merge_with_local=True)

# Query accounts
accounts = manager.search_accounts(broker="Exness")
for acc in accounts:
    print(acc.name, acc.login, acc.server)
```

---

## 💬 Query Accounts Qua AI Chat

Sau khi load accounts từ Sheets, bạn có thể hỏi AI:

### Ví Dụ 1: Query theo Broker

**User:**
```
Cho tôi xem thông tin tài khoản Exness
```

**AI Response:**
```json
{
  "action": "QUERY_ACCOUNT",
  "broker": "Exness",
  "confidence": 1.0,
  "reason": "User wants to see Exness account information"
}
```

**Kết quả**: Hiển thị tất cả tài khoản Exness với đầy đủ thông tin

### Ví Dụ 2: Query theo Login

**User:**
```
Tài khoản login 12345678 có server gì?
```

**AI Response:**
```json
{
  "action": "QUERY_ACCOUNT",
  "login": "12345678",
  "confidence": 1.0,
  "reason": "User wants to know server for account 12345678"
}
```

**Kết quả**: Hiển thị thông tin tài khoản 12345678 bao gồm server

### Ví Dụ 3: Query theo Platform

**User:**
```
Các tài khoản MT5 nào đang có?
```

**AI Response:**
```json
{
  "action": "QUERY_ACCOUNT",
  "platform": "MT5",
  "confidence": 1.0,
  "reason": "User wants to see all MT5 accounts"
}
```

**Kết quả**: Liệt kê tất cả tài khoản MT5

---

## 🔐 Đăng Nhập Sau Khi Query

### Workflow hoàn chỉnh:

**Bước 1: Query để xem thông tin**

```
User: Cho tôi xem tài khoản Exness
AI: [Hiển thị danh sách tài khoản Exness]

Tìm thấy 3 tài khoản Exness:
1. Login: 12345678, Server: Exness-MT5Live, Platform: MT5
2. Login: 87654321, Server: Exness-MT5Real, Platform: MT5
3. Login: 11111111, Server: Exness-MT4Live, Platform: MT4
```

**Bước 2: User chọn tài khoản để login**

```
User: Đăng nhập tài khoản Exness login 12345678
AI: [Tìm thông tin từ Sheets]
```

**Nếu có password trong Sheets:**
```json
{
  "action": "LOGIN_ACCOUNT",
  "platform": "MT5",
  "broker": "Exness",
  "login": "12345678",
  "password": "MyPass123",  # Lấy từ Sheets
  "server": "Exness-MT5Live",  # Lấy từ Sheets
  "confidence": 0.98,
  "reason": "Complete account information found in database",
  "requires_confirmation": true
}
```

**Nếu không có password:**
```json
{
  "action": "REQUEST_INFO",
  "reason": "Found account but missing password",
  "metadata": {
    "missing_fields": ["password"],
    "found_info": {
      "login": "12345678",
      "broker": "Exness",
      "server": "Exness-MT5Live",
      "platform": "MT5"
    },
    "question": "Tài khoản Exness 12345678 đã tìm thấy (server: Exness-MT5Live), vui lòng cung cấp mật khẩu để đăng nhập."
  }
}
```

**Bước 3: User xác nhận**

```
System: [Popup confirmation]
Bạn có muốn đăng nhập tài khoản:
- Broker: Exness
- Login: 12345678
- Platform: MT5
- Server: Exness-MT5Live

[Yes] [No]
```

**Bước 4: Thực thi**

```
System: ✅ Đã gửi yêu cầu đăng nhập tài khoản 12345678
```

---

## 🔄 Refresh Accounts

Để cập nhật dữ liệu từ Google Sheets (khi có thay đổi):

**Qua GUI:**
- Click nút **"Refresh from Sheets"**

**Qua AI Chat:**
```
User: Cập nhật dữ liệu từ Google Sheets
AI: [Thực hiện refresh]
```

**Qua code:**
```python
manager.refresh_from_sheets()
```

---

## 📊 Architecture

```
┌──────────────────┐
│  Google Sheets   │
│  - Account Data  │
└────────┬─────────┘
         │
         ▼
┌────────────────────┐
│  SheetsManager     │
│  - Connect         │
│  - Load Data       │
│  - Parse to DF     │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  AccountManager    │
│  - Merge Accounts  │
│  - Search/Query    │
│  - Save to JSON    │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  AI Chat           │
│  - QUERY_ACCOUNT   │
│  - LOGIN_ACCOUNT   │
└────────────────────┘
```

---

## 🛠️ Troubleshooting

### Lỗi: "Không tìm thấy credentials.json"

**Nguyên nhân**: File credentials.json không có hoặc đặt sai vị trí

**Giải pháp**:
```bash
# Check file có tồn tại không
ls /home/user/JARVIS/credentials.json

# Nếu không có, download lại từ Google Cloud Console
# Đổi tên thành credentials.json
# Copy vào /home/user/JARVIS/
```

### Lỗi: "Permission denied"

**Nguyên nhân**: Service Account chưa được share quyền truy cập Sheet

**Giải pháp**:
1. Mở file `credentials.json`
2. Copy email service account
3. Vào Google Sheet → Share
4. Paste email → Send

### Lỗi: "Could not find worksheet"

**Nguyên nhân**: Tên worksheet trong config không khớp

**Giải pháp**:
- Kiểm tra tên worksheet (tab) trong Google Sheet
- Update `worksheet_name` trong config
- Lưu ý: Tên phải khớp chính xác (case-sensitive)

### Accounts không load được

**Nguyên nhân**: Format Google Sheet không đúng

**Giải pháp**:
- Đảm bảo có header row
- Có ít nhất các cột: Login, Broker
- Không có dòng trống ở đầu
- Header ở dòng 1 (hoặc update `header_row` trong config)

---

## 🎯 Best Practices

### 1. Bảo Mật

- ❌ **KHÔNG** commit `credentials.json` lên git
- ✅ Thêm vào `.gitignore`:
  ```
  credentials.json
  *.json
  config/*.json
  ```

- ❌ **KHÔNG** lưu password trong Google Sheets nếu Sheet có nhiều người truy cập
- ✅ Sử dụng Sheet riêng cho từng người
- ✅ Hoặc để password trống, nhập thủ công khi login

### 2. Performance

- Load accounts **1 lần** khi khởi động
- Cache trong memory
- Refresh khi cần (không phải mỗi query)

### 3. Data Management

- **Google Sheets** = Master data (source of truth)
- **config/accounts.json** = Local cache
- Merge mode: Giữ local changes + sync từ Sheets

---

## 📝 Example Config

File `config/ai_config.json` đầy đủ:

```json
{
  "ai_provider": "mock",

  "google_sheets": {
    "enabled": true,
    "sheet_url": "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit",
    "worksheet_name": "Accounts",
    "header_row": 1,
    "auto_load_on_startup": true,
    "credentials_path": "credentials.json"
  },

  "openai": {
    "api_key": "sk-YOUR-KEY",
    "model": "gpt-3.5-turbo"
  },

  "mt_executor": {
    "speed_settings": {
      "focus_delay": 0.5,
      "key_delay": 0.1,
      "form_open_delay": 1.0,
      "field_delay": 0.2
    }
  },

  "security": {
    "strict_mode": true,
    "require_confirmation_for_login": true
  }
}
```

---

## ✅ Checklist Setup

- [ ] Tạo Google Cloud Project
- [ ] Enable Google Sheets API
- [ ] Tạo Service Account
- [ ] Download credentials.json
- [ ] Copy credentials.json vào /home/user/JARVIS/
- [ ] Share Google Sheet với service account email
- [ ] Tạo/update config/ai_config.json
- [ ] Test kết nối: `python -m core.sheets_manager`
- [ ] Chạy JARVIS: `python mt_login_gui.py`
- [ ] Kiểm tra accounts đã load trong GUI
- [ ] Test query qua AI chat

---

## 🎉 Hoàn Thành!

Bây giờ bạn có thể:

1. ✅ Load tài khoản từ Google Sheets tự động
2. ✅ Query thông tin tài khoản qua AI chat
3. ✅ Đăng nhập nhanh chỉ với "Đăng nhập Exness 12345678"
4. ✅ AI tự động tìm server, platform từ database
5. ✅ Chỉ cần nhập password (nếu không lưu trong Sheets)

**Next Steps**:
- Thêm nhiều tài khoản vào Google Sheets
- Test các query commands
- Customize theo nhu cầu

---

**Created by: JARVIS Team**
**Last Updated: 2025-12-31**
