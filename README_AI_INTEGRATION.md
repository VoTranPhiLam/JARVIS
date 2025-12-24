# 🤖 JARVIS - MT4/MT5 AI Automation System

## Tổng Quan

JARVIS là hệ thống tự động hóa quản lý tài khoản MT4/MT5 với tích hợp AI, cho phép người dùng điều khiển bằng ngôn ngữ tự nhiên.

### Đặc Điểm Chính

✨ **AI-Powered**: Điều khiển bằng ngôn ngữ tự nhiên (tiếng Việt/English)
🔒 **An Toàn**: AI chỉ đưa ra quyết định, Python thực thi với validation
🎯 **Chính Xác**: JSON Command Schema chuẩn, dễ debug
⚡ **Nhanh**: PyQt5 GUI với multi-threading
🔧 **Mở Rộng**: Dễ dàng thêm lệnh mới và AI providers

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │ Natural Language
       ▼
┌─────────────────────────────────────────┐
│          CHAT UI (PyQt5)                │
│  - Chat Display                         │
│  - Input Field                          │
│  - Command Preview Panel                │
└──────┬──────────────────────────────────┘
       │ User Message
       ▼
┌─────────────────────────────────────────┐
│         AI CLIENT                       │
│  - OpenAI / Anthropic / Ollama / Mock   │
│  - System Prompts                       │
└──────┬──────────────────────────────────┘
       │ JSON Response
       ▼
┌─────────────────────────────────────────┐
│      COMMAND VALIDATOR                  │
│  - Schema Validation                    │
│  - Security Checks                      │
│  - Risk Assessment                      │
└──────┬──────────────────────────────────┘
       │ Valid Command
       ▼
┌─────────────────────────────────────────┐
│         MT EXECUTOR                     │
│  - Platform Detection                   │
│  - UI Automation (pywinauto)            │
│  - Login Execution                      │
└─────────────────────────────────────────┘
```

### Nguyên Tắc Thiết Kế

**AI = Decision Only, Python = Execution Only**

- ✅ AI phân tích câu lệnh → trả về JSON
- ✅ Python validate JSON → thực thi
- ❌ AI KHÔNG được phép thao tác UI trực tiếp
- ❌ Python KHÔNG đoán ý định người dùng

---

## 📁 Cấu Trúc Dự Án

```
JARVIS/
├── ai_integration/              # AI Integration Module
│   ├── __init__.py
│   ├── command_schema.py        # JSON Command Schema định nghĩa
│   ├── ai_client.py             # AI Client (OpenAI/Anthropic/Ollama)
│   ├── command_validator.py    # Validation & Security
│   └── system_prompts.py        # System Prompts cho AI
│
├── gui/                         # PyQt5 GUI
│   ├── __init__.py
│   ├── chat_widget.py           # Chat UI Component
│   └── main_window.py           # Main Application Window
│
├── core/                        # Business Logic
│   ├── __init__.py
│   ├── mt_executor.py           # MT4/MT5 Command Executor
│   └── account_manager.py       # Account Management
│
├── config/                      # Configuration Files
│   ├── ai_config.json           # AI Configuration
│   └── accounts.json            # Saved Accounts
│
├── mt_login.py                  # Legacy Script (still works)
├── mt_login_gui.py              # NEW: Main Entry Point
├── requirements.txt
└── README_AI_INTEGRATION.md     # This file
```

---

## 🚀 Cài Đặt và Sử Dụng

### 1. Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

### 2. Cài Đặt AI Provider (Tùy Chọn)

**Mock Mode** (Mặc định - không cần API key):
```bash
# Không cần cài thêm gì, chạy ngay
```

**OpenAI**:
```bash
pip install openai>=1.0.0
```

**Anthropic Claude**:
```bash
pip install anthropic>=0.8.0
```

**Ollama (Local LLM)**:
```bash
# 1. Cài Ollama: https://ollama.ai
# 2. Pull model:
ollama pull llama2
```

### 3. Cấu Hình

Chỉnh sửa `config/ai_config.json`:

```json
{
  "ai_provider": "mock",  // hoặc "openai", "anthropic", "ollama"

  "openai": {
    "api_key": "sk-YOUR-API-KEY",
    "model": "gpt-3.5-turbo"
  },

  "anthropic": {
    "api_key": "sk-ant-YOUR-API-KEY",
    "model": "claude-3-sonnet-20240229"
  }
}
```

### 4. Chạy Ứng Dụng

```bash
python mt_login_gui.py
```

---

## 💬 Ví Dụ Hội Thoại

### Ví Dụ 1: Đăng Nhập Tài Khoản (Đầy Đủ Thông Tin)

**User:**
```
Đăng nhập tài khoản Exness MT5 login 12345678 pass Abc123 server Exness-MT5Live
```

**AI Response (JSON):**
```json
{
  "action": "LOGIN_ACCOUNT",
  "platform": "MT5",
  "broker": "Exness",
  "login": "12345678",
  "password": "Abc123",
  "server": "Exness-MT5Live",
  "confidence": 0.98,
  "reason": "User provided complete login information",
  "requires_confirmation": true,
  "is_safe": true,
  "risk_level": "MEDIUM",
  "raw_user_input": "Đăng nhập tài khoản Exness MT5 login 12345678 pass Abc123 server Exness-MT5Live"
}
```

**System:**
```
✅ Command hợp lệ: LOGIN_ACCOUNT
[Hiển thị popup xác nhận]
→ User xác nhận → Thực thi đăng nhập
```

---

### Ví Dụ 2: Đăng Nhập (Thiếu Thông Tin)

**User:**
```
Login XM MT4 account 567890
```

**AI Response (JSON):**
```json
{
  "action": "REQUEST_INFO",
  "confidence": 1.0,
  "reason": "Missing password and server information",
  "requires_confirmation": false,
  "is_safe": true,
  "risk_level": "LOW",
  "metadata": {
    "missing_fields": ["password", "server"],
    "question": "Để đăng nhập tài khoản XM MT4 567890, vui lòng cung cấp:\n- Mật khẩu (password)\n- Tên server (ví dụ: XM-Real 3)"
  },
  "raw_user_input": "Login XM MT4 account 567890"
}
```

**User:** *(tiếp tục)*
```
Pass là MyPass123, server XM-Real 3
```

**AI Response:**
```json
{
  "action": "LOGIN_ACCOUNT",
  "platform": "MT4",
  "broker": "XM",
  "login": "567890",
  "password": "MyPass123",
  "server": "XM-Real 3",
  "confidence": 0.95,
  "reason": "User completed missing information",
  "requires_confirmation": true,
  "is_safe": true,
  "risk_level": "MEDIUM"
}
```

---

### Ví Dụ 3: Các Lệnh Khác

**Xem Danh Sách Tài Khoản:**
```
User: Cho tôi xem danh sách tài khoản
AI: { "action": "LIST_ACCOUNTS", ... }
```

**Quét Terminal:**
```
User: Quét các terminal đang chạy
AI: { "action": "SCAN_TERMINALS", ... }
```

---

## 🔒 Bảo Mật

### Các Lớp Bảo Vệ

1. **System Prompt Security**
   - AI được huấn luyện KHÔNG tự ý hành động
   - LUÔN hỏi lại khi thiếu thông tin
   - KHÔNG đoán password

2. **Command Validator**
   - Kiểm tra schema đầy đủ
   - Detect dangerous patterns (rm -rf, shutdown, etc.)
   - Whitelist brokers (strict mode)
   - Risk assessment

3. **User Confirmation**
   - Login command → YÊU CẦU xác nhận
   - Hiển thị rõ thông tin trước khi thực thi

4. **No Direct UI Access**
   - AI chỉ trả JSON
   - Python kiểm soát 100% execution

### Risk Levels

- **LOW**: Xem thông tin (LIST, SCAN, STATUS)
- **MEDIUM**: Đăng nhập, thay đổi tài khoản
- **HIGH**: Xóa, reset, thay đổi hệ thống (hiện không có)

---

## 🎨 JSON Command Schema

### Định Nghĩa Chuẩn

```json
{
  // === REQUIRED FIELDS ===
  "action": "LOGIN_ACCOUNT",       // CommandType enum
  "confidence": 0.95,               // 0.0 - 1.0
  "reason": "User wants to login", // Lý do AI đưa ra lệnh

  // === OPTIONAL FIELDS (depends on action) ===
  "platform": "MT5",                // MT4 | MT5 | ANY
  "broker": "Exness",
  "login": "12345678",
  "password": "MyPass123",
  "server": "Exness-MT5Live",

  // === SAFETY FIELDS ===
  "requires_confirmation": true,    // Cần xác nhận?
  "is_safe": true,
  "risk_level": "MEDIUM",           // LOW | MEDIUM | HIGH

  // === METADATA ===
  "metadata": {},                   // Thông tin thêm
  "raw_user_input": "..."           // Câu gốc của user
}
```

### Các Command Types

| Action | Description | Required Fields | Risk |
|--------|-------------|-----------------|------|
| `LOGIN_ACCOUNT` | Đăng nhập tài khoản | platform, login, password, server | MEDIUM |
| `LIST_ACCOUNTS` | Liệt kê tài khoản | - | LOW |
| `SCAN_TERMINALS` | Quét terminals | - | LOW |
| `CHECK_STATUS` | Kiểm tra status | - | LOW |
| `REQUEST_INFO` | Yêu cầu info từ user | metadata.question | LOW |

---

## 🔧 Mở Rộng

### 1. Thêm AI Provider Mới

Chỉnh sửa `ai_integration/ai_client.py`:

```python
def _init_provider(self):
    if self.provider == "your_provider":
        # Initialize your AI client here
        pass

def _your_provider_response(self, user_message, context):
    # Implement API call
    # Return JSON string
    pass
```

### 2. Thêm Command Type Mới

**Bước 1**: Update `ai_integration/command_schema.py`:

```python
class CommandType(Enum):
    # ... existing ...
    YOUR_NEW_COMMAND = "YOUR_NEW_COMMAND"
```

**Bước 2**: Update `ai_integration/system_prompts.py`:

```python
# Thêm mô tả command vào MAIN_SYSTEM_PROMPT
```

**Bước 3**: Implement trong `core/mt_executor.py`:

```python
def execute_command(self, command):
    if action == CommandType.YOUR_NEW_COMMAND.value:
        return self.your_new_function(command)
```

### 3. Tùy Chỉnh UI

Chỉnh sửa `gui/chat_widget.py` hoặc `gui/main_window.py`:

```python
# Thay đổi colors, fonts, layouts
self.chat_display.setStyleSheet("...")
```

---

## 🐛 Debug

### Enable Debug Mode

Thêm vào đầu `mt_login_gui.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Riêng Từng Module

**Test Command Schema:**
```bash
python -m ai_integration.command_schema
```

**Test AI Client (Mock):**
```bash
python -m ai_integration.ai_client
```

**Test Command Validator:**
```bash
python -m ai_integration.command_validator
```

**Test Chat Widget (Standalone):**
```bash
python -m gui.chat_widget
```

**Test MT Executor:**
```bash
python -m core.mt_executor
```

---

## 📊 Performance

- **GUI**: PyQt5 với multi-threading → không block UI
- **AI**: Background thread cho API calls
- **MT Automation**: Configurable speed settings

Tùy chỉnh tốc độ trong `config/ai_config.json`:

```json
{
  "mt_executor": {
    "speed_settings": {
      "focus_delay": 0.5,       // Thời gian focus window
      "key_delay": 0.1,         // Delay giữa các phím
      "form_open_delay": 1.0,   // Đợi form mở
      "field_delay": 0.2        // Delay giữa các field
    }
  }
}
```

---

## 🎯 Roadmap

### Phase 1: Core ✅ (Hoàn Thành)
- [x] JSON Command Schema
- [x] AI Integration (Mock/OpenAI/Anthropic/Ollama)
- [x] Command Validator
- [x] PyQt5 Chat UI
- [x] MT Executor
- [x] Account Manager

### Phase 2: Enhancement
- [ ] Encrypted password storage
- [ ] Multi-language support (full i18n)
- [ ] Voice input
- [ ] Trade operation commands (open/close positions)
- [ ] Scheduled automation
- [ ] Advanced analytics dashboard

### Phase 3: AI Evolution
- [ ] Context-aware AI (remember past conversations)
- [ ] Auto-suggest based on patterns
- [ ] Anomaly detection
- [ ] Self-learning from user feedback

---

## 📝 License

MIT License - Free to use and modify

---

## 👥 Contributors

- JARVIS Team
- AI Integration: Senior Python Engineer
- UI Design: PyQt5 Specialist

---

## 📞 Support

Gặp vấn đề? Tạo issue trên GitHub hoặc liên hệ team.

---

## ⚠️ Disclaimer

Phần mềm này chỉ dùng cho mục đích automation cá nhân. Người dùng chịu trách nhiệm tuân thủ điều khoản của broker. Không bảo đảm lợi nhuận trading.

---

**Enjoy JARVIS! 🚀**
