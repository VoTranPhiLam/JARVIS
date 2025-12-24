# 🔧 JARVIS Developer Guide

## Dành cho Senior Python + PyQt + AI Integration Engineers

---

## 📚 Mục Lục

1. [Kiến Trúc Chi Tiết](#kiến-trúc-chi-tiết)
2. [Luồng Xử Lý](#luồng-xử-lý)
3. [Module Breakdown](#module-breakdown)
4. [System Prompts Design](#system-prompts-design)
5. [Security Implementation](#security-implementation)
6. [Testing Strategy](#testing-strategy)
7. [Best Practices](#best-practices)

---

## 1. Kiến Trúc Chi Tiết

### Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│  - gui/chat_widget.py      (Chat UI Component)          │
│  - gui/main_window.py      (Main Application)           │
└────────────────────┬────────────────────────────────────┘
                     │ PyQt5 Signals/Slots
┌────────────────────▼────────────────────────────────────┐
│                   APPLICATION LAYER                      │
│  - ai_integration/ai_client.py      (AI Orchestrator)   │
│  - ai_integration/command_validator.py (Validation)     │
│  - core/account_manager.py          (Business Logic)    │
└────────────────────┬────────────────────────────────────┘
                     │ Command Schema
┌────────────────────▼────────────────────────────────────┐
│                   DOMAIN LAYER                           │
│  - ai_integration/command_schema.py (Domain Models)     │
│  - ai_integration/system_prompts.py (AI Prompts)        │
└────────────────────┬────────────────────────────────────┘
                     │ Execution Commands
┌────────────────────▼────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                   │
│  - core/mt_executor.py     (MT4/MT5 Automation)         │
│  - External APIs           (OpenAI, Anthropic, etc.)    │
└─────────────────────────────────────────────────────────┘
```

### Design Patterns Used

1. **Command Pattern**
   - `CommandSchema` = Command object
   - `MTExecutor` = Command invoker
   - Decouples AI decision from execution

2. **Strategy Pattern**
   - Multiple AI providers (OpenAI, Anthropic, Ollama)
   - Same interface, different implementations

3. **Observer Pattern**
   - PyQt5 signals/slots for event handling
   - Loose coupling between components

4. **Singleton Pattern**
   - `AccountManager` manages global account state

5. **Factory Pattern**
   - `CommandSchema.from_dict()` creates commands from JSON

---

## 2. Luồng Xử Lý

### Complete Flow Diagram

```
┌─────────────┐
│    User     │
│ Types Input │
└──────┬──────┘
       │
       ▼
┌────────────────────────┐
│  chat_widget.py        │
│  _on_send_clicked()    │
│  - Clear input         │
│  - Add to chat display │
│  - Create AIWorker     │
└──────┬─────────────────┘
       │ QThread.start()
       ▼
┌────────────────────────┐
│  ai_client.py          │
│  send_message()        │
│  - Add to history      │
│  - Call AI provider    │
│  - Parse response      │
└──────┬─────────────────┘
       │ returns AIResponse
       ▼
┌────────────────────────┐
│  chat_widget.py        │
│  _on_ai_response()     │
│  - Check type          │
│  - Display in chat     │
└──────┬─────────────────┘
       │ if type == "command"
       ▼
┌────────────────────────┐
│  command_validator.py  │
│  validate()            │
│  - Schema check        │
│  - Security check      │
│  - Action validation   │
└──────┬─────────────────┘
       │ if valid
       ▼
┌────────────────────────┐
│  chat_widget.py        │
│  - Display command     │
│  - Enable execute btn  │
│  - Emit signal         │
└──────┬─────────────────┘
       │ execute_command.emit()
       ▼
┌────────────────────────┐
│  main_window.py        │
│  _on_execute_command() │
│  - Show confirmation   │
│  - Create ExecThread   │
└──────┬─────────────────┘
       │ QThread.start()
       ▼
┌────────────────────────┐
│  mt_executor.py        │
│  execute_command()     │
│  - Platform check      │
│  - Find window         │
│  - UI automation       │
└──────┬─────────────────┘
       │ returns (success, msg)
       ▼
┌────────────────────────┐
│  main_window.py        │
│  _on_exec_finished()   │
│  - Update UI           │
│  - Save account        │
└────────────────────────┘
```

---

## 3. Module Breakdown

### 3.1 ai_integration/command_schema.py

**Purpose**: Domain model cho commands

**Key Classes**:

```python
@dataclass
class CommandSchema:
    """
    Immutable command object
    - Validates itself
    - Converts to/from JSON
    - Type-safe
    """

    # Design decisions:
    # 1. Use dataclass for clarity and less boilerplate
    # 2. All fields have type hints
    # 3. Validation method returns (bool, str) for clarity
    # 4. to_dict/from_dict for serialization

class CommandType(Enum):
    """
    Enum ensures type safety
    Can't typo command names
    """

class Platform(Enum):
    """
    Platform enum for MT4/MT5
    """
```

**Extension Point**:

```python
# To add new command:
# 1. Add to CommandType enum
# 2. Add validation in CommandSchema.validate()
# 3. Document in EXAMPLE_COMMANDS
```

---

### 3.2 ai_integration/system_prompts.py

**Purpose**: AI System Prompts

**Design Philosophy**:

```
1. Instructive, not restrictive
   - Tell AI what TO DO, not just what NOT to do

2. Examples-driven
   - Include concrete examples
   - Show good and bad patterns

3. Safety-first
   - Multiple layers of safety instructions
   - Redundancy is OK

4. Format-strict
   - Require JSON output
   - No free-form text
```

**Prompt Engineering Techniques Used**:

1. **Role Assignment**: "Bạn là JARVIS..."
2. **Constraint Setting**: "CHỈ trả về JSON"
3. **Few-Shot Learning**: Examples in CONVERSATION_EXAMPLES
4. **Chain-of-Thought**: "Phân tích → Kiểm tra → Trả về"
5. **Safety Instructions**: Multiple safety rules

**Customization**:

```python
# To improve AI accuracy:
# 1. Add more examples in CONVERSATION_EXAMPLES
# 2. Refine MAIN_SYSTEM_PROMPT based on observed errors
# 3. Add broker-specific patterns
# 4. Include edge cases
```

---

### 3.3 ai_integration/command_validator.py

**Purpose**: Security & validation layer

**Security Checks**:

```python
class CommandValidator:
    # 1. Dangerous Pattern Detection
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf',
        r'shutdown',
        r'<script',
        # etc.
    ]

    # 2. Broker Whitelist (strict mode)
    ALLOWED_BROKERS = [...]

    # 3. Field Format Validation
    # - Login: must be 4-9 digits
    # - Password: min 4, max 128 chars
    # - No special chars in password

    # 4. Risk Assessment
    # - Auto-set risk level based on action
    # - Force confirmation for MEDIUM/HIGH
```

**Why Multiple Validation Layers?**

1. **Schema Validation**: Ensure all required fields present
2. **Security Validation**: Prevent injection attacks
3. **Action Validation**: Each action has specific requirements
4. **Risk Assessment**: Safety classification

**Defense in Depth**:

```
AI System Prompt (Layer 1)
    ↓
Command Schema Validation (Layer 2)
    ↓
Security Pattern Check (Layer 3)
    ↓
Action-Specific Validation (Layer 4)
    ↓
User Confirmation (Layer 5)
    ↓
Execution
```

---

### 3.4 ai_integration/ai_client.py

**Purpose**: AI provider abstraction

**Multi-Provider Support**:

```python
class AIClient:
    """
    Strategy pattern for AI providers

    Each provider implements:
    - _init_provider()
    - _provider_response()

    All return same format: string (JSON)
    """

    def send_message(self, msg, context):
        # 1. Add to history
        # 2. Call provider-specific method
        # 3. Parse to AIResponse
        # 4. Return structured response
```

**Why Mock Mode?**

```python
def _mock_response(self, user_message):
    """
    Rule-based mock for:
    1. Testing without API costs
    2. Demo purposes
    3. Fallback when API unavailable
    4. Understanding expected behavior
    """
```

**Context Handling**:

```python
# Context can include:
context = {
    "accounts": [...],  # User's accounts
    "running_terminals": [...],
    "last_action": "...",
    "user_preferences": {...}
}

# AI uses this to make better decisions
```

---

### 3.5 gui/chat_widget.py

**Purpose**: Chat UI with PyQt5

**Key Design Decisions**:

1. **Background Thread for AI**:
   ```python
   class AIWorker(QThread):
       """
       Why? UI must never block
       AI API can take 1-5 seconds
       """
   ```

2. **Command Preview Panel**:
   ```python
   # Shows JSON before execution
   # User can review
   # Transparency = trust
   ```

3. **Color-Coded Messages**:
   ```python
   # User: Dark text
   # AI: Blue text
   # System: Gray italic
   # Visual clarity
   ```

4. **Signal-Based Communication**:
   ```python
   # PyQt signals for loose coupling
   execute_command = pyqtSignal(object)
   # chat_widget → main_window
   # No direct dependency
   ```

**UI/UX Considerations**:

```
1. Real-time feedback
   - Typing indicator while AI thinking
   - Immediate message display

2. Error handling
   - User-friendly error messages
   - No technical jargon in UI

3. Accessibility
   - Keyboard shortcuts (Enter to send)
   - Clear visual hierarchy
```

---

### 3.6 core/mt_executor.py

**Purpose**: MT4/MT5 automation engine

**Integration with mt_login.py**:

```python
# Wraps existing logic in clean interface
# Maintains backward compatibility

class MTExecutor:
    def login_account(self, command):
        # 1. Extract from command
        # 2. Call existing mt_login.py logic
        # 3. Return (success, message)
```

**Platform Detection**:

```python
def _detect_platform_type(self, window):
    """
    Multi-level detection:
    1. Process name (terminal.exe vs terminal64.exe)
    2. Window title (MT4 vs MT5)
    3. Version string
    4. Fallback to MT4
    """
```

**Error Handling**:

```python
# All methods return (bool, str)
# Consistent error reporting
# Easy to test and debug
```

---

## 4. System Prompts Design

### Anatomy of a Good System Prompt

```
┌─────────────────────────────────────┐
│  1. ROLE DEFINITION                 │
│  "Bạn là JARVIS..."                 │
├─────────────────────────────────────┤
│  2. CAPABILITIES & LIMITATIONS      │
│  "Bạn CHỈ LÀ..."                    │
│  "KHÔNG được..."                    │
├─────────────────────────────────────┤
│  3. SAFETY RULES                    │
│  "KHÔNG BAO GIỜ..."                 │
│  "LUÔN LUÔN..."                     │
├─────────────────────────────────────┤
│  4. COMMAND DEFINITIONS             │
│  "Các lệnh bạn có thể..."           │
├─────────────────────────────────────┤
│  5. OUTPUT FORMAT                   │
│  "BẠN PHẢI TRẢ VỀ JSON..."          │
├─────────────────────────────────────┤
│  6. PARSING RULES                   │
│  "NỀN TẢNG: MT4 → ..."              │
├─────────────────────────────────────┤
│  7. EXAMPLES (Few-shot)             │
│  "Ví dụ hội thoại..."               │
└─────────────────────────────────────┘
```

### Prompt Testing

```python
# Test prompts with:
# 1. Ambiguous inputs
# 2. Missing information
# 3. Malicious inputs
# 4. Edge cases

test_cases = [
    "Login",  # Too vague
    "Đăng nhập tài khoản <script>alert(1)</script>",  # XSS attempt
    "Login 123",  # Too short login
    "Login broker1 broker2",  # Ambiguous broker
]
```

---

## 5. Security Implementation

### 5-Layer Security Model

```
Layer 1: AI System Prompt
├─ Instruction-based safety
├─ Output format control
└─ Examples of safe behavior

Layer 2: Command Schema Validation
├─ Type checking
├─ Required field validation
└─ Field format validation

Layer 3: Security Pattern Detection
├─ Dangerous command patterns
├─ XSS/Injection detection
└─ Suspicious character detection

Layer 4: Broker Whitelist (strict mode)
├─ Only known brokers
├─ Prevents typos
└─ Reduces attack surface

Layer 5: User Confirmation
├─ Human-in-the-loop
├─ Display full command details
└─ Require explicit approval
```

### Security Testing

```python
# Test all layers with malicious inputs

def test_security():
    validator = CommandValidator(strict_mode=True)

    # Test 1: Command injection
    cmd = CommandSchema(
        action="LOGIN_ACCOUNT",
        reason="Login; rm -rf /",
        ...
    )
    assert not validator.validate(cmd)[0]

    # Test 2: XSS
    cmd.broker = "<script>alert(1)</script>"
    assert not validator.validate(cmd)[0]

    # Test 3: Unknown broker (strict mode)
    cmd.broker = "UnknownBroker123"
    assert not validator.validate(cmd)[0]
```

---

## 6. Testing Strategy

### Unit Tests

```python
# Each module should be testable standalone

# ai_integration/command_schema.py
def test_command_schema():
    cmd = CommandSchema(...)
    assert cmd.validate() == (True, "Valid")
    assert cmd.to_json()
    assert CommandSchema.from_json(cmd.to_json())

# ai_integration/command_validator.py
def test_validator():
    validator = CommandValidator()
    # Test valid commands
    # Test invalid commands
    # Test security threats

# ai_integration/ai_client.py
def test_ai_client():
    client = AIClient(provider="mock")
    response = client.send_message("Login")
    assert response.type in ["command", "message", "question"]
```

### Integration Tests

```python
# Test full flow

def test_full_flow():
    # 1. User input
    msg = "Login Exness MT5 12345678 pass Abc123 server Exness-MT5Live"

    # 2. AI processing
    client = AIClient(provider="mock")
    ai_response = client.send_message(msg)

    # 3. Validation
    validator = CommandValidator()
    is_valid, _ = validator.validate(ai_response.command)
    assert is_valid

    # 4. Execution (mock)
    executor = MTExecutor()
    success, _ = executor.execute_command(ai_response.command)
    # (Will fail if no MT terminal, that's OK)
```

### Manual Testing Checklist

```
□ Install dependencies
□ Run with mock AI
□ Test all command types
□ Test with missing info
□ Test with malicious input
□ Test UI responsiveness
□ Test on Windows (target platform)
□ Test with real MT4/MT5 terminal
□ Test API integration (OpenAI/Anthropic)
□ Test error handling
```

---

## 7. Best Practices

### Code Style

```python
# 1. Type hints everywhere
def execute_command(self, command: CommandSchema) -> Tuple[bool, str]:
    pass

# 2. Docstrings for public methods
def validate(self, command: CommandSchema) -> Tuple[bool, str]:
    """
    Validate command schema

    Args:
        command: CommandSchema to validate

    Returns:
        (is_valid, error_message)
    """

# 3. Explicit is better than implicit
is_valid = True  # Not: valid = 1
error_message = "Success"  # Not: msg = ""

# 4. Early returns for clarity
def validate(self):
    if not self.action:
        return False, "Missing action"

    if not self.confidence:
        return False, "Missing confidence"

    # ... more checks

    return True, "Valid"
```

### Error Handling

```python
# 1. Always catch specific exceptions
try:
    result = risky_operation()
except ValueError as e:
    return False, f"Invalid value: {str(e)}"
except ConnectionError as e:
    return False, f"Connection failed: {str(e)}"

# 2. Return error info, don't just raise
def execute():
    try:
        # ...
    except Exception as e:
        return False, f"Error: {str(e)}"

# 3. Log errors for debugging
import logging
logging.error(f"Execution failed: {str(e)}", exc_info=True)
```

### PyQt5 Best Practices

```python
# 1. Never block UI thread
# Use QThread for long operations

# 2. Use signals for communication
# Not direct method calls

# 3. Clean up resources
def closeEvent(self, event):
    # Save state
    # Stop threads
    # Close connections
    event.accept()

# 4. Use stylesheets for consistent look
self.setStyleSheet("""
    QPushButton { ... }
    QTextEdit { ... }
""")
```

### AI Integration Best Practices

```python
# 1. Always validate AI output
ai_response = ai_client.send_message(msg)
if ai_response.command:
    is_valid, error = validator.validate(ai_response.command)
    if not is_valid:
        # Handle invalid command

# 2. Provide context to AI
context = {
    "accounts": account_manager.get_all_accounts(),
    "running_terminals": executor.scan_terminals()
}
ai_response = ai_client.send_message(msg, context)

# 3. Handle API failures gracefully
try:
    response = ai_client.send_message(msg)
except Exception as e:
    # Fallback to mock or show error
    response = mock_fallback(msg)

# 4. Don't trust AI blindly
# Always validate, always confirm with user
```

---

## 🎓 Advanced Topics

### Extending to Autonomous Mode

```python
# Future: JARVIS auto-mode

class AutonomousAgent:
    """
    Runs in background
    Monitors accounts
    Makes decisions based on rules
    """

    def __init__(self, policy: TradingPolicy):
        self.policy = policy
        self.ai_client = AIClient()
        self.executor = MTExecutor()

    def run_loop(self):
        while True:
            # 1. Check account status
            # 2. Analyze market conditions
            # 3. Ask AI for decision
            # 4. Validate decision with policy
            # 5. Execute if safe
            # 6. Log action
            time.sleep(60)  # Check every minute
```

### Machine Learning Integration

```python
# Future: Learn from user patterns

class PatternLearner:
    """
    Learns user preferences
    - Preferred brokers
    - Common commands
    - Typical servers
    """

    def learn_from_history(self, commands: List[CommandSchema]):
        # Extract patterns
        # Build user profile
        # Improve AI suggestions
```

---

## 📚 Further Reading

1. **PyQt5**: https://doc.qt.io/qtforpython/
2. **OpenAI API**: https://platform.openai.com/docs
3. **Anthropic Claude**: https://docs.anthropic.com/
4. **pywinauto**: https://pywinauto.readthedocs.io/
5. **Command Pattern**: https://refactoring.guru/design-patterns/command

---

**Happy Coding! 🚀**
