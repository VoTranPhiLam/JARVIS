# 📊 Google Sheets Integration - Status Report

---

## ✅ HOÀN THÀNH (Đã commit & push)

### 1. Core Modules

#### ✅ `core/sheets_manager.py` (430 lines)
**Chức năng**:
- Connect đến Google Sheets API
- Load data từ worksheet
- Parse thành pandas DataFrame
- Search & filter accounts
- Auto-mapping từ Sheets format sang Account format

**Methods chính**:
```python
- connect(sheet_url, worksheet_name)
- load_data(data_range, header_row)
- get_accounts(filter_dict)
- search_accounts(query)
- find_account(login, broker, platform)
- get_stats()
- refresh()
```

#### ✅ `core/account_manager.py` (Cập nhật +220 lines)
**Thêm chức năng**:
- Tích hợp SheetsManager
- Google Sheets methods:
  * `connect_sheets()` - Kết nối
  * `load_from_sheets()` - Load & merge accounts
  * `refresh_from_sheets()` - Refresh data
- Query methods:
  * `search_accounts(query, broker, platform, login)` - Tìm kiếm nâng cao
  * `get_account_info(login, broker)` - Lấy thông tin chi tiết
  * `get_stats()` - Thống kê

**Usage**:
```python
# Initialize với Sheets support
manager = AccountManager(use_sheets=True)

# Connect
manager.connect_sheets(sheet_url, "Sheet1")

# Load accounts
manager.load_from_sheets(merge_with_local=True)

# Query
accounts = manager.search_accounts(broker="Exness")
info = manager.get_account_info("12345678")
```

### 2. AI Integration

#### ✅ `ai_integration/command_schema.py`
**Thêm**:
- `CommandType.QUERY_ACCOUNT` enum
- Fields mới trong CommandSchema:
  * `query: Optional[str]` - Text search
  * `query_params: Optional[Dict]` - Additional params

**Example command**:
```json
{
  "action": "QUERY_ACCOUNT",
  "broker": "Exness",
  "login": "12345678",
  "query": "tài khoản MT5",
  "confidence": 1.0,
  "reason": "User wants to query account info"
}
```

#### ✅ `ai_integration/system_prompts.py`
**Thêm**:
1. QUERY_ACCOUNT vào danh sách lệnh với hướng dẫn chi tiết
2. 3 conversation examples mới:
   - Example 5: Query theo broker
   - Example 6: Query theo login
   - Example 7: Query theo platform

**AI biết cách**:
- Phân biệt QUERY (hỏi thông tin) vs LOGIN (thực hiện đăng nhập)
- Trả về QUERY_ACCOUNT khi user hỏi thông tin
- Extract broker, login, platform từ câu hỏi

### 3. Documentation

#### ✅ `GOOGLE_SHEETS_INTEGRATION_GUIDE.md` (550+ lines)
**Nội dung đầy đủ**:
- Setup Google Cloud Project
- Create Service Account
- Download credentials.json
- Share Sheet với service account
- Cấu trúc Google Sheet chuẩn
- Config JARVIS
- Usage examples
- Query commands
- Workflow: Query → Confirm → Login
- Troubleshooting
- Best practices
- Checklist setup

---

## ⏳ ĐANG LÀM (Cần hoàn thành)

### 1. Update MT Executor

**File**: `core/mt_executor.py`

**Cần thêm**:
```python
def execute_command(self, command: CommandSchema):
    # ... existing code ...

    elif action == CommandType.QUERY_ACCOUNT.value:
        return self.query_account(command)

def query_account(self, command: CommandSchema) -> Tuple[bool, str]:
    """Handle QUERY_ACCOUNT command"""
    # Get accounts from AccountManager
    # Format results
    # Return formatted string
```

**Lý do**: MT Executor cần biết cách xử lý QUERY_ACCOUNT để trả về kết quả

---

### 2. Update Command Validator

**File**: `ai_integration/command_validator.py`

**Cần thêm**:
```python
def _validate_action(self, command):
    # ... existing code ...

    elif action == CommandType.QUERY_ACCOUNT.value:
        return self._validate_query_action(command)

def _validate_query_action(self, command) -> Tuple[bool, str]:
    """Validate QUERY_ACCOUNT command"""
    # QUERY_ACCOUNT không cần password
    # Ít nhất phải có 1 trong: query, broker, login, platform
    if not any([command.query, command.broker, command.login, command.platform]):
        return False, "QUERY_ACCOUNT needs at least one query parameter"

    return True, "Valid query command"
```

**Lý do**: Validator cần rules riêng cho QUERY_ACCOUNT

---

### 3. Update AI Client Mock Mode

**File**: `ai_integration/ai_client.py`

**Cần thêm** vào `_mock_response()`:
```python
elif any(word in user_lower for word in ['thông tin', 'xem', 'có']):
    # QUERY_ACCOUNT logic
    result = {
        "action": "QUERY_ACCOUNT",
        "confidence": 0.9,
        "reason": "User wants to query account info",
        ...
    }

    # Extract params from user message
    if 'exness' in user_lower:
        result["broker"] = "Exness"

    login_match = re.search(r'\d{4,9}', user_message)
    if login_match:
        result["login"] = login_match.group()

    return json.dumps(result)
```

**Lý do**: Mock mode cần biết cách tạo QUERY_ACCOUNT command

---

### 4. Update Main Window GUI

**File**: `gui/main_window.py`

**Cần thêm**:

**A. Load Sheets on startup**:
```python
def __init__(self, ...):
    # ... existing code ...

    # Load Google Sheets if enabled
    self._load_from_sheets_if_enabled()

def _load_from_sheets_if_enabled(self):
    """Load accounts from Google Sheets if configured"""
    try:
        import json
        with open('config/ai_config.json') as f:
            config = json.load(f)

        sheets_config = config.get('google_sheets', {})
        if sheets_config.get('enabled') and sheets_config.get('auto_load_on_startup'):
            sheet_url = sheets_config.get('sheet_url')
            worksheet = sheets_config.get('worksheet_name', 'Sheet1')

            if sheet_url:
                self.account_manager.connect_sheets(sheet_url, worksheet)
                self.account_manager.load_from_sheets()
                self._load_accounts()  # Refresh table
    except Exception as e:
        print(f"Could not load from sheets: {e}")
```

**B. Add buttons**:
```python
# Thêm trong _create_account_panel():
sheets_btn = QPushButton("🔄 Refresh from Sheets")
sheets_btn.clicked.connect(self._on_refresh_sheets)
button_layout.addWidget(sheets_btn)
```

**C. Handle QUERY_ACCOUNT results**:
```python
def _on_execution_finished(self, success: bool, message: str):
    # ... existing code ...

    # If QUERY_ACCOUNT, display results in chat
    if self.executor_thread.command.action == CommandType.QUERY_ACCOUNT.value:
        self.chat_widget.add_execution_result(success, message)
        # Optionally highlight accounts in table
```

---

### 5. Update Chat Widget

**File**: `gui/chat_widget.py`

**Cần thêm**:
```python
def display_query_results(self, accounts: List[Account]):
    """Display query results in chat"""
    if not accounts:
        self._add_system_message("Không tìm thấy tài khoản nào")
        return

    result_text = f"Tìm thấy {len(accounts)} tài khoản:\n\n"
    for i, acc in enumerate(accounts, 1):
        result_text += f"{i}. {acc.broker} - Login: {acc.login}\n"
        result_text += f"   Platform: {acc.platform}, Server: {acc.server}\n"
        if acc.name:
            result_text += f"   Name: {acc.name}\n"
        result_text += "\n"

    self._add_ai_message(result_text)
```

---

## 🎯 WORKFLOW HOÀN CHỈNH (Khi tất cả done)

### Scenario 1: Query rồi Login

```
Step 1: User hỏi thông tin
User: "Cho tôi xem tài khoản Exness"

Step 2: AI trả về QUERY_ACCOUNT
{
  "action": "QUERY_ACCOUNT",
  "broker": "Exness",
  ...
}

Step 3: MT Executor query từ AccountManager
accounts = account_manager.search_accounts(broker="Exness")

Step 4: Hiển thị kết quả
Chat: "Tìm thấy 3 tài khoản Exness:
  1. Login 12345678, Server: Exness-MT5Live
  2. Login 87654321, Server: Exness-Real
  3. ..."

Step 5: User chọn login
User: "Đăng nhập tài khoản 12345678"

Step 6: AI trả về LOGIN_ACCOUNT (có đầy đủ info từ database)
{
  "action": "LOGIN_ACCOUNT",
  "broker": "Exness",
  "login": "12345678",
  "server": "Exness-MT5Live",  # Lấy từ database
  "platform": "MT5",            # Lấy từ database
  "password": "..."              # Hoặc hỏi user nếu không có
}

Step 7: User confirm → Execute
```

---

## 🔧 CÁCH TEST

### Test 1: SheetsManager Standalone

```bash
cd /home/user/JARVIS

# Test connect (cần credentials.json và sheet URL thật)
python -c "
from core.sheets_manager import SheetsManager

manager = SheetsManager()
sheet_url = 'YOUR_SHEET_URL'
manager.connect(sheet_url, 'Sheet1')
manager.load_data()

accounts = manager.get_accounts()
print(f'Loaded {len(accounts)} accounts')
for acc in accounts[:3]:
    print(acc)
"
```

### Test 2: AccountManager với Sheets

```bash
python -c "
from core import AccountManager

manager = AccountManager(use_sheets=True)
manager.connect_sheets('YOUR_SHEET_URL', 'Sheet1')
manager.load_from_sheets()

# Search
results = manager.search_accounts(broker='Exness')
print(f'Found {len(results)} Exness accounts')

# Get info
info = manager.get_account_info('12345678')
print(info)
"
```

### Test 3: Full Integration (Sau khi hoàn thành tất cả)

```bash
python mt_login_gui.py

# Trong chat:
1. "Cho tôi xem tài khoản Exness"
   → Expect: Hiển thị danh sách Exness accounts

2. "Tài khoản login 12345678 có server gì?"
   → Expect: Hiển thị thông tin account 12345678

3. "Đăng nhập tài khoản Exness 12345678"
   → Expect: AI tìm thông tin từ DB → Login
```

---

## 📝 CHECKLIST HOÀN THÀNH

### Core Features
- [x] SheetsManager - Connect & load data
- [x] AccountManager - Sheets integration
- [x] QUERY_ACCOUNT command schema
- [x] AI prompts cho QUERY
- [x] Documentation guide

### Remaining
- [ ] MT Executor - Handle QUERY_ACCOUNT
- [ ] Command Validator - Validate QUERY
- [ ] AI Client - Mock mode cho QUERY
- [ ] Main Window - Load sheets on startup
- [ ] Main Window - Refresh sheets button
- [ ] Chat Widget - Display query results
- [ ] End-to-end testing
- [ ] Update README_AI_INTEGRATION.md

---

## 🚀 NEXT STEPS

### Để hoàn thành 100%:

1. **Finish MT Executor** (15 mins)
   - Add query_account() method
   - Format results nicely

2. **Finish Command Validator** (5 mins)
   - Add _validate_query_action()

3. **Finish AI Client Mock** (10 mins)
   - Add QUERY logic to _mock_response()

4. **Finish GUI Updates** (20 mins)
   - Add load_from_sheets_if_enabled()
   - Add refresh button
   - Handle query results display

5. **Testing** (15 mins)
   - Test with real Google Sheet
   - Test query commands
   - Test full workflow

**Total estimate**: ~1 hour

---

## 💡 TIPS

### Để test ngay không cần GUI:

```python
# Test script
from core import AccountManager

# Load from sheets
mgr = AccountManager(use_sheets=True)
mgr.connect_sheets('YOUR_URL', 'Sheet1')
mgr.load_from_sheets()

# Query
accounts = mgr.search_accounts(broker="Exness")
for acc in accounts:
    print(f"{acc.broker} - {acc.login} - {acc.server}")
```

### Config mẫu (config/ai_config.json):

```json
{
  "google_sheets": {
    "enabled": true,
    "sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_ID/edit",
    "worksheet_name": "Sheet1",
    "auto_load_on_startup": true
  }
}
```

---

## 📞 Support

Nếu cần tiếp tục hoàn thành:
1. Xem GOOGLE_SHEETS_INTEGRATION_GUIDE.md
2. Follow checklist trên
3. Test từng module trước khi integrate

**Status**: 60% complete, core features ready, remaining is UI integration and testing.

---

**Last Updated**: 2025-12-31
**Branch**: claude/mt4-mt5-automation-GRWbZ
**Latest Commit**: feat: Add Google Sheets Integration & QUERY_ACCOUNT Command
