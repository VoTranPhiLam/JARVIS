# 📖 HƯỚNG DẪN SỬ DỤNG JARVIS - MT4/MT5 AI AUTOMATION

**Phiên bản**: 1.0.0
**Ngày cập nhật**: 2025-01-01

---

## 📋 MỤC LỤC

1. [Giới Thiệu](#giới-thiệu)
2. [Cài Đặt](#cài-đặt)
3. [Cấu Hình](#cấu-hình)
4. [Khởi Động Ứng Dụng](#khởi-động-ứng-dụng)
5. [Hướng Dẫn Sử Dụng Chi Tiết](#hướng-dẫn-sử-dụng-chi-tiết)
6. [Các Tính Năng](#các-tính-năng)
7. [Ví Dụ Thực Tế](#ví-dụ-thực-tế)
8. [Xử Lý Lỗi](#xử-lý-lỗi)
9. [Câu Hỏi Thường Gặp](#câu-hỏi-thường-gặp)

---

## 🎯 GIỚI THIỆU

JARVIS là hệ thống tự động hóa MT4/MT5 sử dụng AI, cho phép bạn:

✅ **Đăng nhập tài khoản MT4/MT5** bằng câu lệnh tiếng Việt
✅ **Quản lý danh sách tài khoản** từ Google Sheets
✅ **Truy vấn thông tin tài khoản** qua AI chat
✅ **Quét terminal đang chạy** tự động
✅ **Sử dụng AI thật** (OpenAI/Claude) hoặc Mock mode miễn phí

---

## 🔧 CÀI ĐẶT

### Bước 1: Yêu Cầu Hệ Thống

- **Hệ điều hành**: Windows 10/11
- **Python**: 3.8 trở lên
- **MT4/MT5**: Đã cài đặt trên máy

### Bước 2: Cài Đặt Python Dependencies

```bash
# Mở Command Prompt hoặc PowerShell tại thư mục JARVIS
cd C:\path\to\JARVIS

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### Bước 3: Cài Đặt AI Provider (Tùy Chọn)

**Nếu muốn dùng OpenAI:**
```bash
pip install openai>=1.0.0
```

**Nếu muốn dùng Anthropic Claude:**
```bash
pip install anthropic>=0.8.0
```

**Lưu ý**: Bạn có thể bỏ qua bước này và sử dụng **Mock Mode** (AI giả lập miễn phí).

---

## ⚙️ CẤU HÌNH

### Cấu Hình AI (Quan Trọng!)

#### Option 1: Sử dụng Mock Mode (Không Cần API Key)

Mock mode sử dụng AI giả lập (rule-based), hoàn toàn miễn phí, phù hợp để học và test.

1. Mở file `config/ai_config.json`
2. Đảm bảo cấu hình như sau:

```json
{
  "ai_provider": "mock",

  "openai": {
    "api_key": "YOUR_OPENAI_API_KEY_HERE",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
  },

  "anthropic": {
    "api_key": "YOUR_ANTHROPIC_API_KEY_HERE",
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

#### Option 2: Sử dụng OpenAI (Cần API Key)

1. Lấy API key từ: https://platform.openai.com/api-keys
2. Mở file `config/ai_config.json`
3. Sửa như sau:

```json
{
  "ai_provider": "openai",

  "openai": {
    "api_key": "sk-YOUR-REAL-API-KEY-HERE",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

#### Option 3: Sử dụng Anthropic Claude (Cần API Key)

1. Lấy API key từ: https://console.anthropic.com/
2. Mở file `config/ai_config.json`
3. Sửa như sau:

```json
{
  "ai_provider": "anthropic",

  "anthropic": {
    "api_key": "sk-ant-YOUR-REAL-API-KEY-HERE",
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### Cấu Hình Google Sheets (Tùy Chọn)

Nếu muốn load tài khoản từ Google Sheets, xem file:
- `GOOGLE_SHEETS_INTEGRATION_GUIDE.md`

---

## 🚀 KHỞI ĐỘNG ỨNG DỤNG

### Cách 1: Chạy từ Python

```bash
python mt_login_gui.py
```

### Cách 2: Build thành EXE (Nếu cần)

```bash
python build_exe.py
```

Sau đó chạy file `JARVIS.exe` trong thư mục `dist/`.

### Kiểm Tra Khởi Động

Khi chạy thành công, bạn sẽ thấy:

```
================================================================================
⚡ JARVIS - MT4/MT5 AI Automation System ⚡
================================================================================

AI Provider: openai    (hoặc mock/anthropic)

✅ Application started successfully
================================================================================
```

---

## 📚 HƯỚNG DẪN SỬ DỤNG CHI TIẾT

### Giao Diện Chính

Khi ứng dụng mở, bạn sẽ thấy:

```
┌─────────────────────────────────────────────────────────────┐
│  JARVIS - MT4/MT5 Automation                          [ _ □ X ]│
├────────────────────┬────────────────────────────────────────┤
│                    │  💬 AI Chat                            │
│  📋 Account List   │                                        │
│                    │  AI: Xin chào! Tôi có thể giúp gì?    │
│  [+] Add Account   │                                        │
│  [ ] Exness 12345  │  You: Cho tôi xem danh sách tài khoản │
│  [ ] XM 98765      │                                        │
│                    │  AI: Đây là danh sách...               │
│  [Scan Terminal]   │                                        │
│  [Load Sheets]     │  ┌──────────────────────────────────┐ │
│                    │  │ Command Preview (JSON)           │ │
│                    │  │ {                                │ │
│                    │  │   "action": "LIST_ACCOUNTS"      │ │
│                    │  │ }                                │ │
│                    │  └──────────────────────────────────┘ │
│                    │                                        │
│                    │  Your message: _____________________ ⏎│
│                    │  [▶ Execute Command]                   │
└────────────────────┴────────────────────────────────────────┘
```

### Luồng Hoạt Động Cơ Bản

1. **Gõ câu lệnh** vào ô chat (tiếng Việt hoặc English)
2. **AI phân tích** và trả lời trong chat
3. **Xem Command Preview** (JSON) để kiểm tra AI hiểu đúng chưa
4. **Nhấn Execute** để thực thi lệnh
5. **Xác nhận** (nếu lệnh yêu cầu)
6. **Xem kết quả** trong chat

---

## 🎮 CÁC TÍNH NĂNG

### 1️⃣ Xem Danh Sách Tài Khoản

**Câu lệnh:**
```
Cho tôi xem danh sách tài khoản
Xem danh sách account
List all accounts
```

**Kết quả:**
```
📋 Danh sách tài khoản (3):

1. Exness - Login: 12345678
   Platform: MT5
   Server: Exness-MT5Live
   Status: active

2. XM - Login: 98765432
   Platform: MT4
   Server: XMGlobal-Real
   Status: active
```

---

### 2️⃣ Truy Vấn Thông Tin Tài Khoản (QUERY_ACCOUNT)

**Câu lệnh:**
```
Cho tôi xem thông tin tài khoản Exness
Tài khoản nào có login 12345678?
Server của tài khoản XM là gì?
Xem tài khoản MT5
```

**Ví dụ chi tiết:**

**Input:**
```
You: Cho tôi xem thông tin tài khoản Exness
```

**Output:**
```
AI: 📋 Tìm thấy 2 tài khoản Exness:

1. Exness - Login: 12345678
   Platform: MT5
   Server: Exness-MT5Live
   Status: active

2. Exness - Login: 87654321
   Platform: MT4
   Server: Exness-MT4Real
   Status: active
```

**Command Preview:**
```json
{
  "action": "QUERY_ACCOUNT",
  "broker": "Exness",
  "confidence": 0.95,
  "reason": "User wants to query Exness account information"
}
```

---

### 3️⃣ Đăng Nhập Tài Khoản

#### Cách 1: Cung cấp đầy đủ thông tin

**Câu lệnh:**
```
Đăng nhập tài khoản Exness MT5 login 12345678 pass MyPass123 server Exness-MT5Live
```

**Kết quả:**
```
AI: ✅ Đã nhận đủ thông tin đăng nhập:
- Broker: Exness
- Platform: MT5
- Login: 12345678
- Password: ******** (đã ẩn)
- Server: Exness-MT5Live

Nhấn "Execute Command" để thực hiện đăng nhập.
```

**Command Preview:**
```json
{
  "action": "LOGIN_ACCOUNT",
  "platform": "MT5",
  "broker": "Exness",
  "login": "12345678",
  "password": "MyPass123",
  "server": "Exness-MT5Live",
  "confidence": 0.98,
  "requires_confirmation": true
}
```

**Nhấn Execute** → Popup xác nhận → Chọn "Yes" → Terminal tự động đăng nhập!

---

#### Cách 2: Cung cấp từng bước (Multi-turn)

**Bước 1:**
```
You: Đăng nhập tài khoản Exness MT5 login 12345678
```

**AI:**
```
AI: ⚠️ Thiếu thông tin:
- Password: Chưa có
- Server: Chưa có

Vui lòng cung cấp thêm.
```

**Bước 2:**
```
You: Pass là MyPass123, server Exness-MT5Live
```

**AI:**
```
AI: ✅ Đã nhận đủ thông tin! Nhấn "Execute Command" để đăng nhập.
```

---

### 4️⃣ Quét Terminal Đang Chạy

**Câu lệnh:**
```
Quét các terminal MT4/MT5 đang chạy
Scan terminal
Kiểm tra terminal nào đang mở
```

**Kết quả:**
```
🔍 Tìm thấy 2 terminal đang chạy:

1. Exness-MT5Live (MT5)
   Path: C:\Program Files\Exness MT5\terminal64.exe
   PID: 12345

2. XMGlobal-Real (MT4)
   Path: C:\Program Files\XM MT4\terminal.exe
   PID: 67890
```

---

### 5️⃣ Load Tài Khoản từ Google Sheets

**Bước 1: Chuẩn bị Google Sheets**

Tạo sheet với format:

| Broker | Platform | Login     | Password  | Server          | Status |
|--------|----------|-----------|-----------|-----------------|--------|
| Exness | MT5      | 12345678  | MyPass123 | Exness-MT5Live  | active |
| XM     | MT4      | 98765432  | XmPass456 | XMGlobal-Real   | active |

**Bước 2: Cấu hình Service Account**

Xem hướng dẫn chi tiết trong: `GOOGLE_SHEETS_INTEGRATION_GUIDE.md`

**Bước 3: Load vào ứng dụng**

Có 2 cách:

**Cách 1: Qua GUI**
1. Nhấn nút **"Load Sheets"**
2. Nhập URL của Google Sheet
3. Nhập tên Worksheet (mặc định: "Sheet1")
4. Chọn "Merge with local" nếu muốn giữ tài khoản cũ
5. Nhấn "Load"

**Cách 2: Qua AI Chat**
```
You: Load tài khoản từ Google Sheets
```

**Kết quả:**
```
✅ Đã load 15 tài khoản từ Google Sheets
📋 Danh sách đã được cập nhật
```

---

### 6️⃣ Thêm Tài Khoản Thủ Công

**Cách 1: Qua GUI**
1. Nhấn nút **"[+] Add Account"**
2. Điền thông tin:
   - Broker: Exness
   - Platform: MT5
   - Login: 12345678
   - Password: MyPass123
   - Server: Exness-MT5Live
3. Nhấn "Save"

**Cách 2: Qua AI Chat**
```
You: Thêm tài khoản mới Exness MT5 login 12345678 server Exness-MT5Live
AI: Bạn muốn lưu tài khoản này vào danh sách?
You: Có
```

---

## 💡 VÍ DỤ THỰC TẾ

### Ví Dụ 1: Workflow Hoàn Chỉnh

**Mục tiêu**: Đăng nhập vào tất cả tài khoản Exness

**Bước 1: Query tài khoản**
```
You: Cho tôi xem tất cả tài khoản Exness
```

**AI trả lời:**
```
📋 Tìm thấy 3 tài khoản Exness:

1. Exness - Login: 12345678 (MT5, Exness-MT5Live)
2. Exness - Login: 23456789 (MT5, Exness-MT5Real)
3. Exness - Login: 34567890 (MT4, Exness-MT4Real)
```

**Bước 2: Đăng nhập từng tài khoản**
```
You: Đăng nhập tài khoản Exness MT5 login 12345678 pass MyPass1 server Exness-MT5Live
AI: ✅ Sẵn sàng đăng nhập
[Execute] → [Yes] → ✅ Đăng nhập thành công!

You: Tiếp theo đăng nhập 23456789 pass MyPass2 server Exness-MT5Real
AI: ✅ Sẵn sàng đăng nhập
[Execute] → [Yes] → ✅ Đăng nhập thành công!

You: Cuối cùng đăng nhập 34567890 MT4 pass MyPass3 server Exness-MT4Real
AI: ✅ Sẵn sàng đăng nhập
[Execute] → [Yes] → ✅ Đăng nhập thành công!
```

---

### Ví Dụ 2: Tìm Kiếm Tài Khoản Cụ Thể

**Tình huống**: Bạn có nhiều tài khoản, muốn tìm server của login 87654321

**Input:**
```
You: Server của tài khoản có login 87654321 là gì?
```

**Output:**
```
AI: 📋 Tìm thấy 1 tài khoản:

XM - Login: 87654321
Platform: MT4
Server: XMGlobal-Real 47
Status: active
```

---

### Ví Dụ 3: Load Hàng Loạt từ Google Sheets

**Tình huống**: Bạn có 50 tài khoản trong Google Sheets, muốn import hết

**Bước 1: Chuẩn bị Sheet**
```
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

**Bước 2: Load vào JARVIS**
```
1. Nhấn "Load Sheets"
2. Paste URL sheet
3. Chọn "Merge with local accounts"
4. Nhấn "Load"
```

**Kết quả:**
```
✅ Đã load 50 tài khoản từ Google Sheets
✅ Merged với 5 tài khoản local
📋 Tổng cộng: 55 tài khoản
```

**Bước 3: Query để kiểm tra**
```
You: Có bao nhiêu tài khoản MT5?
AI: 📋 Tìm thấy 32 tài khoản MT5
```

---

## ⚠️ XỬ LÝ LỖI

### Lỗi 1: "Module not found: PyQt5"

**Nguyên nhân**: Chưa cài đặt dependencies

**Giải pháp:**
```bash
pip install -r requirements.txt
```

---

### Lỗi 2: "API key not configured"

**Nguyên nhân**: Chưa cấu hình API key trong `config/ai_config.json`

**Giải pháp:**
1. Mở file `config/ai_config.json`
2. Thay thế `YOUR_OPENAI_API_KEY_HERE` bằng API key thật
3. Hoặc chuyển sang `"ai_provider": "mock"`

---

### Lỗi 3: "Cannot find MT4/MT5 window"

**Nguyên nhân**:
- Chưa mở terminal MT4/MT5
- Tên broker không khớp với tiêu đề cửa sổ

**Giải pháp:**
1. Mở MT4/MT5 terminal trước
2. Kiểm tra tiêu đề cửa sổ (ví dụ: "Exness-MT5Live")
3. Dùng tên broker trong lệnh phải khớp với tiêu đề
4. Ví dụ: Nếu cửa sổ là "XMGlobal-Real", dùng broker "XM" hoặc "XMGlobal"

---

### Lỗi 4: "Google Sheets API error"

**Nguyên nhân**:
- Chưa cấu hình service account
- File `credentials.json` không tồn tại
- Không có quyền truy cập sheet

**Giải pháp:**
1. Xem hướng dẫn trong `GOOGLE_SHEETS_INTEGRATION_GUIDE.md`
2. Đảm bảo file `credentials.json` trong thư mục gốc
3. Share Google Sheet với email service account
4. Kiểm tra URL sheet có đúng không

---

### Lỗi 5: "PyQt5 không chạy được"

**Nguyên nhân**: Thiếu Visual C++ Redistributable

**Giải pháp:**
1. Download và cài đặt:
   https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Restart máy
3. Chạy lại ứng dụng

---

### Lỗi 6: "Permission denied when clicking Execute"

**Nguyên nhân**: Windows UAC chặn automation

**Giải pháp:**
1. Chạy ứng dụng với quyền Administrator (Right-click → Run as Administrator)
2. Hoặc tắt UAC tạm thời (không khuyến khích)

---

## ❓ CÂU HỎI THƯỜNG GẶP

### Q1: Mock mode khác gì so với OpenAI/Claude?

**Mock mode:**
- ✅ Miễn phí 100%
- ✅ Không cần API key
- ✅ Hoạt động offline
- ❌ Chỉ nhận diện pattern cơ bản
- ❌ Không học được từ ngữ mới

**OpenAI/Claude:**
- ✅ Hiểu ngữ cảnh phức tạp
- ✅ Học được cách bạn nói chuyện
- ✅ Xử lý câu lệnh tự nhiên hơn
- ❌ Cần API key (tính phí)
- ❌ Cần internet

**Khuyến nghị**: Dùng Mock mode để học, sau đó chuyển sang OpenAI/Claude khi thành thạo.

---

### Q2: Tôi có thể dùng tiếng Anh không?

**Trả lời**: Có! Hệ thống hỗ trợ cả tiếng Việt và tiếng Anh.

**Ví dụ:**
```
✅ Login Exness MT5 12345678 pass MyPass server Exness-MT5Live
✅ Đăng nhập Exness MT5 12345678 pass MyPass server Exness-MT5Live
✅ Show me all Exness accounts
✅ Cho tôi xem tất cả tài khoản Exness
```

---

### Q3: Password có được lưu không?

**Trả lời**:
- Password **KHÔNG** được lưu trong `config/accounts.json` vì lý do bảo mật
- Mỗi lần đăng nhập, bạn phải cung cấp password
- Nếu dùng Google Sheets, password được lưu trong sheet (nên encrypt sheet)

---

### Q4: Tôi có thể tự động đăng nhập nhiều tài khoản cùng lúc không?

**Trả lời**: Hiện tại chưa hỗ trợ đăng nhập parallel. Bạn phải đăng nhập từng tài khoản một.

**Workaround**:
- Query tất cả tài khoản cần đăng nhập
- Copy/paste lệnh đăng nhập và thay đổi thông tin
- Execute từng lệnh

---

### Q5: Google Sheets có bắt buộc không?

**Trả lời**: Không! Google Sheets là tùy chọn. Bạn có thể:
- Thêm tài khoản thủ công qua GUI
- Hoặc edit file `config/accounts.json` trực tiếp
- Hoặc dùng Google Sheets nếu có nhiều tài khoản

---

### Q6: Ứng dụng có hoạt động trên Mac/Linux không?

**Trả lời**: Không. Ứng dụng chỉ chạy trên Windows vì sử dụng `pywinauto` để tương tác với MT4/MT5.

---

### Q7: Tôi có thể thêm broker mới không?

**Trả lời**: Có! Hệ thống tự động nhận diện broker từ tiêu đề cửa sổ MT4/MT5. Chỉ cần:
1. Mở terminal broker mới
2. Xem tiêu đề cửa sổ (ví dụ: "ICMarkets-Live")
3. Dùng tên broker trong lệnh: "ICMarkets" hoặc "IC Markets"

---

### Q8: Command Preview là gì? Tại sao cần kiểm tra?

**Trả lời**: Command Preview hiển thị JSON command mà AI tạo ra. Bạn nên kiểm tra để:
- Đảm bảo AI hiểu đúng ý bạn
- Phát hiện sai sót (sai login, sai server, v.v.)
- Học cách AI phân tích lệnh

**Ví dụ AI hiểu sai:**
```
You: Đăng nhập tài khoản 12345678
AI tạo: {"broker": "Exness", "login": "12345678", ...}
```
→ Bạn kiểm tra thấy broker sai (phải là XM chứ không phải Exness)
→ Gõ lại: "Đăng nhập tài khoản XM 12345678"

---

### Q9: Tôi có thể customize AI prompts không?

**Trả lời**: Có! Edit file `ai_integration/system_prompts.py` để:
- Thêm ví dụ lệnh mới
- Thay đổi cách AI phản hồi
- Train AI hiểu cách nói của bạn

---

### Q10: Làm sao để backup dữ liệu tài khoản?

**Trả lời**: Dữ liệu tài khoản được lưu trong `config/accounts.json`. Để backup:

```bash
# Backup
cp config/accounts.json config/accounts.backup.json

# Restore
cp config/accounts.backup.json config/accounts.json
```

Hoặc sử dụng Google Sheets làm backup tự động.

---

## 🎓 TIPS & TRICKS

### Tip 1: Sử dụng Mock Mode để học

Mock mode không tốn tiền, phù hợp để:
- Hiểu cách hệ thống hoạt động
- Luyện tập gõ lệnh
- Test workflow

Sau khi thành thạo, chuyển sang OpenAI/Claude để trải nghiệm tốt hơn.

---

### Tip 2: Query trước khi login

Luôn query tài khoản trước khi đăng nhập để:
- Kiểm tra thông tin chính xác
- Tránh nhầm lẫn login/server
- Xem danh sách tài khoản có sẵn

**Ví dụ:**
```
You: Xem tài khoản Exness
AI: [Hiển thị 3 tài khoản Exness]
You: Đăng nhập tài khoản đầu tiên
AI: [Tự động điền thông tin từ query]
```

---

### Tip 3: Lưu Command Preview vào Notepad

Nếu bạn thường xuyên đăng nhập cùng 1 tập tài khoản:
1. Query tài khoản
2. Copy JSON command
3. Lưu vào Notepad
4. Lần sau paste vào chat

---

### Tip 4: Dùng Google Sheets để quản lý nhóm tài khoản

Tạo nhiều worksheet cho các nhóm khác nhau:
- **Sheet1**: Tài khoản Live
- **Sheet2**: Tài khoản Demo
- **Sheet3**: Tài khoản Backup

Load worksheet cần thiết khi dùng.

---

### Tip 5: Kiểm tra Command Preview trước khi Execute

**LUÔN LUÔN** kiểm tra JSON command trước khi nhấn Execute để:
- Đảm bảo broker đúng
- Kiểm tra login đúng
- Xác nhận server chính xác

**Một lỗi nhỏ** trong JSON có thể dẫn đến đăng nhập sai tài khoản!

---

### Tip 6: Sử dụng Multi-turn conversation cho bảo mật

Thay vì gõ password trong câu lệnh đầu tiên (có thể bị log), hãy:
1. Gõ lệnh không có password
2. AI hỏi password
3. Gõ password trong tin nhắn riêng

**Ví dụ:**
```
You: Đăng nhập Exness MT5 12345678 server Exness-MT5Live
AI: Thiếu password
You: Pass là MySecretPass123    ← Tin nhắn riêng, ít rủi ro hơn
```

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề không có trong hướng dẫn:

1. Kiểm tra file log (nếu có)
2. Xem thêm tài liệu:
   - `README_AI_INTEGRATION.md` - Chi tiết về AI integration
   - `DEVELOPER_GUIDE.md` - Dành cho developers
   - `GOOGLE_SHEETS_INTEGRATION_GUIDE.md` - Hướng dẫn Google Sheets
3. Report issue trên GitHub (nếu có)

---

## 🎉 KẾT LUẬN

JARVIS giúp bạn tự động hóa việc quản lý tài khoản MT4/MT5 một cách thông minh và an toàn.

**Những điều quan trọng cần nhớ:**
- ✅ Kiểm tra Command Preview trước khi Execute
- ✅ Backup dữ liệu tài khoản thường xuyên
- ✅ Sử dụng Mock mode để học trước
- ✅ Query trước, login sau
- ✅ Không share API key với người khác

**Chúc bạn sử dụng hiệu quả! 🚀**

---

**Phiên bản**: 1.0.0
**Cập nhật lần cuối**: 2025-01-01
**Tác giả**: JARVIS Team
