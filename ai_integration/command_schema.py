"""
JSON Command Schema Definition for JARVIS AI Integration

Định nghĩa chuẩn các lệnh mà AI có thể trả về và Python sẽ thực thi.
AI chỉ đưa ra quyết định (decision), Python thực thi (execution).
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import json


class CommandType(Enum):
    """Các loại lệnh được phép"""
    LOGIN_ACCOUNT = "LOGIN_ACCOUNT"
    LOGOUT_ACCOUNT = "LOGOUT_ACCOUNT"
    SWITCH_ACCOUNT = "SWITCH_ACCOUNT"
    LIST_ACCOUNTS = "LIST_ACCOUNTS"
    QUERY_ACCOUNT = "QUERY_ACCOUNT"  # Query thông tin về 1 hoặc nhiều account
    SCAN_TERMINALS = "SCAN_TERMINALS"
    CHECK_STATUS = "CHECK_STATUS"
    REQUEST_INFO = "REQUEST_INFO"
    UNKNOWN = "UNKNOWN"


class Platform(Enum):
    """Nền tảng trading"""
    MT4 = "MT4"
    MT5 = "MT5"
    ANY = "ANY"


@dataclass
class CommandSchema:
    """
    Schema chuẩn cho mọi lệnh từ AI

    Example:
    {
        "action": "LOGIN_ACCOUNT",
        "platform": "MT5",
        "broker": "Exness",
        "login": "12345678",
        "password": "MySecurePass123",
        "server": "Exness-MT5Live",
        "confidence": 0.93,
        "reason": "User requested login via chat",
        "requires_confirmation": False,
        "metadata": {}
    }
    """

    # === REQUIRED FIELDS ===
    action: str  # CommandType
    confidence: float  # 0.0 - 1.0
    reason: str  # Lý do AI đưa ra lệnh này

    # === OPTIONAL FIELDS (depends on action) ===
    platform: Optional[str] = None  # MT4 | MT5 | ANY
    broker: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    server: Optional[str] = None

    # === QUERY FIELDS (for QUERY_ACCOUNT action) ===
    query: Optional[str] = None  # Text search query
    query_params: Optional[Dict[str, str]] = None  # Additional query parameters

    # === SAFETY FIELDS ===
    requires_confirmation: bool = False  # Yêu cầu xác nhận từ user?
    is_safe: bool = True  # Lệnh này có an toàn?
    risk_level: str = "LOW"  # LOW | MEDIUM | HIGH

    # === METADATA ===
    metadata: Optional[Dict[str, Any]] = None  # Thông tin thêm
    raw_user_input: Optional[str] = None  # Câu lệnh gốc của user

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandSchema':
        """Create from dictionary"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'CommandSchema':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> tuple[bool, str]:
        """
        Validate command schema
        Returns: (is_valid, error_message)
        """
        # Check required fields
        if not self.action:
            return False, "Missing required field: action"

        if not isinstance(self.confidence, (int, float)) or not (0 <= self.confidence <= 1):
            return False, "Confidence must be between 0 and 1"

        if not self.reason:
            return False, "Missing required field: reason"

        # Validate action type
        try:
            CommandType(self.action)
        except ValueError:
            return False, f"Invalid action type: {self.action}"

        # Validate platform
        if self.platform:
            try:
                Platform(self.platform)
            except ValueError:
                return False, f"Invalid platform: {self.platform}. Must be MT4, MT5, or ANY"

        # Action-specific validation
        if self.action == CommandType.LOGIN_ACCOUNT.value:
            if not self.login:
                return False, "LOGIN_ACCOUNT requires 'login' field"
            if not self.password:
                return False, "LOGIN_ACCOUNT requires 'password' field"
            if not self.server:
                return False, "LOGIN_ACCOUNT requires 'server' field"
            if not self.platform or self.platform == Platform.ANY.value:
                return False, "LOGIN_ACCOUNT requires specific platform (MT4 or MT5)"

        return True, "Valid"


@dataclass
class AIResponse:
    """
    Response từ AI (có thể chứa command hoặc message)
    """
    type: str  # "command" | "message" | "question"
    content: str  # Text response hoặc JSON command
    command: Optional[CommandSchema] = None
    needs_more_info: bool = False
    missing_fields: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "content": self.content,
            "needs_more_info": self.needs_more_info,
            "missing_fields": self.missing_fields
        }
        if self.command:
            result["command"] = self.command.to_dict()
        return result


# === EXAMPLES ===

EXAMPLE_COMMANDS = {
    "login_account": CommandSchema(
        action=CommandType.LOGIN_ACCOUNT.value,
        platform=Platform.MT5.value,
        broker="Exness",
        login="12345678",
        password="MySecurePass123",
        server="Exness-MT5Live",
        confidence=0.93,
        reason="User requested login to Exness MT5 account 12345678",
        requires_confirmation=False,
        is_safe=True,
        risk_level="LOW",
        metadata={"source": "chat"},
        raw_user_input="Đăng nhập tài khoản Exness MT5 login 12345678"
    ),

    "list_accounts": CommandSchema(
        action=CommandType.LIST_ACCOUNTS.value,
        platform=Platform.ANY.value,
        confidence=1.0,
        reason="User wants to see all accounts",
        requires_confirmation=False,
        is_safe=True,
        risk_level="LOW"
    ),

    "scan_terminals": CommandSchema(
        action=CommandType.SCAN_TERMINALS.value,
        confidence=1.0,
        reason="User wants to scan running MT4/MT5 terminals",
        requires_confirmation=False,
        is_safe=True,
        risk_level="LOW"
    )
}


def print_example_commands():
    """Print example commands for documentation"""
    print("=" * 80)
    print("JARVIS AI COMMAND SCHEMA - EXAMPLES")
    print("=" * 80)

    for name, cmd in EXAMPLE_COMMANDS.items():
        print(f"\n### {name.upper()} ###")
        print(cmd.to_json())
        print()


if __name__ == "__main__":
    print_example_commands()
