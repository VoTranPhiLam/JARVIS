"""
Command Validator for JARVIS AI Integration

Validates and sanitizes commands from AI before execution.
Ensures security and prevents malicious or erroneous commands.
"""

import re
from typing import Tuple, Optional, List
from .command_schema import CommandSchema, CommandType, Platform


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class CommandValidator:
    """
    Validates commands from AI before execution

    Responsibilities:
    1. Schema validation
    2. Security checks
    3. Data sanitization
    4. Risk assessment
    """

    # Security blacklists
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf',
        r'del\s+/f',
        r'format\s+c:',
        r'shutdown',
        r'reboot',
        r'<script',
        r'javascript:',
        r'eval\(',
        r'exec\(',
    ]

    # Allowed broker names (whitelist)
    ALLOWED_BROKERS = [
        'exness', 'xm', 'fbs', 'admirals', 'ic markets',
        'pepperstone', 'fxtm', 'hotforex', 'roboforex',
        'octafx', 'alpari', 'tickmill', 'forex4you',
        'tradingpro', 'skilling'
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator

        Args:
            strict_mode: If True, apply strict validation rules
        """
        self.strict_mode = strict_mode

    def validate(self, command: CommandSchema) -> Tuple[bool, str]:
        """
        Main validation method

        Args:
            command: CommandSchema object to validate

        Returns:
            (is_valid, error_message)
        """
        try:
            # 1. Schema validation
            is_valid, msg = command.validate()
            if not is_valid:
                return False, f"Schema validation failed: {msg}"

            # 2. Security checks
            is_safe, msg = self._check_security(command)
            if not is_safe:
                return False, f"Security check failed: {msg}"

            # 3. Action-specific validation
            is_valid, msg = self._validate_action(command)
            if not is_valid:
                return False, f"Action validation failed: {msg}"

            # 4. Risk assessment
            self._assess_risk(command)

            return True, "Validation passed"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _check_security(self, command: CommandSchema) -> Tuple[bool, str]:
        """
        Check for security threats

        Returns:
            (is_safe, error_message)
        """
        # Check all string fields for dangerous patterns
        fields_to_check = [
            command.broker,
            command.server,
            command.reason,
            command.raw_user_input
        ]

        for field in fields_to_check:
            if field is None:
                continue

            field_str = str(field).lower()

            # Check dangerous patterns
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, field_str, re.IGNORECASE):
                    return False, f"Dangerous pattern detected: {pattern}"

        # Check password field separately (should not contain code)
        if command.password:
            if any(char in command.password for char in ['<', '>', ';', '|', '&']):
                return False, "Password contains suspicious characters"

        return True, "Security check passed"

    def _validate_action(self, command: CommandSchema) -> Tuple[bool, str]:
        """
        Validate specific action requirements

        Returns:
            (is_valid, error_message)
        """
        action = command.action

        if action == CommandType.LOGIN_ACCOUNT.value:
            return self._validate_login_action(command)
        elif action == CommandType.LIST_ACCOUNTS.value:
            return self._validate_list_action(command)
        elif action == CommandType.SCAN_TERMINALS.value:
            return self._validate_scan_action(command)
        elif action == CommandType.CHECK_STATUS.value:
            return self._validate_status_action(command)
        elif action == CommandType.REQUEST_INFO.value:
            return True, "Valid"
        else:
            return False, f"Unknown action: {action}"

    def _validate_login_action(self, command: CommandSchema) -> Tuple[bool, str]:
        """Validate LOGIN_ACCOUNT command"""

        # Required fields check (already done in schema, double check here)
        if not command.login:
            return False, "Missing login"
        if not command.password:
            return False, "Missing password"
        if not command.server:
            return False, "Missing server"
        if not command.platform or command.platform == Platform.ANY.value:
            return False, "Platform must be MT4 or MT5 for login"

        # Validate login format (should be numeric)
        if not re.match(r'^\d{4,9}$', command.login):
            return False, f"Invalid login format: {command.login}. Must be 4-9 digits"

        # Validate password (basic checks)
        if len(command.password) < 4:
            return False, "Password too short (minimum 4 characters)"
        if len(command.password) > 128:
            return False, "Password too long (maximum 128 characters)"

        # Validate broker (whitelist check in strict mode)
        if self.strict_mode and command.broker:
            broker_lower = command.broker.lower()
            if not any(allowed in broker_lower for allowed in self.ALLOWED_BROKERS):
                return False, f"Unknown broker: {command.broker}. Please verify broker name."

        # Safety check - LOGIN should always require confirmation
        if not command.requires_confirmation:
            return False, "LOGIN_ACCOUNT must require confirmation"

        return True, "Valid login command"

    def _validate_list_action(self, command: CommandSchema) -> Tuple[bool, str]:
        """Validate LIST_ACCOUNTS command"""
        # No specific requirements
        return True, "Valid list command"

    def _validate_scan_action(self, command: CommandSchema) -> Tuple[bool, str]:
        """Validate SCAN_TERMINALS command"""
        # No specific requirements
        return True, "Valid scan command"

    def _validate_status_action(self, command: CommandSchema) -> Tuple[bool, str]:
        """Validate CHECK_STATUS command"""
        # No specific requirements
        return True, "Valid status command"

    def _assess_risk(self, command: CommandSchema) -> None:
        """
        Assess and update risk level of command

        Modifies command.risk_level in place
        """
        action = command.action

        # Define risk levels
        if action in [CommandType.LOGIN_ACCOUNT.value, CommandType.SWITCH_ACCOUNT.value]:
            command.risk_level = "MEDIUM"
            command.requires_confirmation = True
        elif action in [CommandType.LIST_ACCOUNTS.value, CommandType.SCAN_TERMINALS.value,
                       CommandType.CHECK_STATUS.value, CommandType.REQUEST_INFO.value]:
            command.risk_level = "LOW"
            command.requires_confirmation = False
        else:
            command.risk_level = "HIGH"
            command.requires_confirmation = True

    def sanitize_command(self, command: CommandSchema) -> CommandSchema:
        """
        Sanitize command data

        Args:
            command: Command to sanitize

        Returns:
            Sanitized command
        """
        # Trim whitespace from string fields
        if command.broker:
            command.broker = command.broker.strip()
        if command.server:
            command.server = command.server.strip()
        if command.login:
            command.login = command.login.strip()

        # Remove any HTML/script tags
        if command.reason:
            command.reason = re.sub(r'<[^>]+>', '', command.reason)

        return command


# Test functions
def test_validator():
    """Test validator with various commands"""
    validator = CommandValidator(strict_mode=True)

    # Test 1: Valid login command
    print("Test 1: Valid login command")
    cmd1 = CommandSchema(
        action=CommandType.LOGIN_ACCOUNT.value,
        platform=Platform.MT5.value,
        broker="Exness",
        login="12345678",
        password="MyPass123",
        server="Exness-MT5Live",
        confidence=0.95,
        reason="User login request",
        requires_confirmation=True
    )
    is_valid, msg = validator.validate(cmd1)
    print(f"  Result: {is_valid}, Message: {msg}\n")

    # Test 2: Invalid login (no password)
    print("Test 2: Invalid login (no password)")
    cmd2 = CommandSchema(
        action=CommandType.LOGIN_ACCOUNT.value,
        platform=Platform.MT5.value,
        broker="Exness",
        login="12345678",
        server="Exness-MT5Live",
        confidence=0.95,
        reason="User login request",
        requires_confirmation=True
    )
    is_valid, msg = validator.validate(cmd2)
    print(f"  Result: {is_valid}, Message: {msg}\n")

    # Test 3: Security threat
    print("Test 3: Security threat in reason field")
    cmd3 = CommandSchema(
        action=CommandType.LIST_ACCOUNTS.value,
        confidence=1.0,
        reason="List accounts; rm -rf /",
        requires_confirmation=False
    )
    is_valid, msg = validator.validate(cmd3)
    print(f"  Result: {is_valid}, Message: {msg}\n")

    # Test 4: Valid list command
    print("Test 4: Valid list command")
    cmd4 = CommandSchema(
        action=CommandType.LIST_ACCOUNTS.value,
        confidence=1.0,
        reason="User wants to see accounts",
        requires_confirmation=False
    )
    is_valid, msg = validator.validate(cmd4)
    print(f"  Result: {is_valid}, Message: {msg}\n")


if __name__ == "__main__":
    test_validator()
