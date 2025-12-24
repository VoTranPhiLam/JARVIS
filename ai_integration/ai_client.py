"""
AI Client for JARVIS

Handles communication with AI providers (OpenAI, Anthropic, Local models, etc.)
Parses natural language to JSON commands.
"""

import json
import re
from typing import Optional, Dict, Any, List
from .command_schema import CommandSchema, AIResponse
from .system_prompts import get_full_system_prompt


class AIClient:
    """
    AI Client for parsing natural language to commands

    Supports multiple providers:
    - OpenAI (GPT-3.5, GPT-4)
    - Anthropic (Claude)
    - Local models (Ollama, LM Studio)
    - Mock mode for testing
    """

    def __init__(
        self,
        provider: str = "mock",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize AI Client

        Args:
            provider: AI provider (openai, anthropic, ollama, mock)
            api_key: API key for cloud providers
            model: Model name
            base_url: Base URL for API (for local models)
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.conversation_history: List[Dict[str, str]] = []

        # Initialize provider client
        self._init_provider()

    def _init_provider(self):
        """Initialize specific provider client"""
        if self.provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                if not self.model:
                    self.model = "gpt-3.5-turbo"
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")

        elif self.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                if not self.model:
                    self.model = "claude-3-sonnet-20240229"
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")

        elif self.provider == "ollama":
            # For Ollama, we'll use requests
            if not self.base_url:
                self.base_url = "http://localhost:11434"
            if not self.model:
                self.model = "llama2"

        elif self.provider == "mock":
            # Mock mode for testing
            self.client = None
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def send_message(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Send message to AI and get response

        Args:
            user_message: User's message
            context: Additional context (account list, etc.)

        Returns:
            AIResponse object
        """
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Get AI response based on provider
        if self.provider == "mock":
            ai_response = self._mock_response(user_message)
        elif self.provider == "openai":
            ai_response = self._openai_response(user_message, context)
        elif self.provider == "anthropic":
            ai_response = self._anthropic_response(user_message, context)
        elif self.provider == "ollama":
            ai_response = self._ollama_response(user_message, context)
        else:
            ai_response = "Error: Unknown provider"

        # Add AI response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": ai_response
        })

        # Parse response to AIResponse
        return self._parse_ai_response(ai_response, user_message)

    def _mock_response(self, user_message: str) -> str:
        """
        Mock AI response for testing (rule-based)

        Args:
            user_message: User's message

        Returns:
            JSON command string
        """
        user_lower = user_message.lower()

        # Mock response based on keywords
        if any(word in user_lower for word in ['đăng nhập', 'login']):
            # Try to extract info
            login_match = re.search(r'\d{4,9}', user_message)
            broker_keywords = ['exness', 'xm', 'fbs', 'admirals']
            broker = next((b for b in broker_keywords if b in user_lower), "unknown")
            platform = "MT5" if "mt5" in user_lower else "MT4"

            if login_match:
                login = login_match.group()
                # Check if has password
                pass_match = re.search(r'pass(?:word)?\s*[:=]?\s*(\S+)', user_lower)
                server_match = re.search(r'server\s*[:=]?\s*([\w-]+)', user_message, re.IGNORECASE)

                if pass_match and server_match:
                    # Complete info
                    return json.dumps({
                        "action": "LOGIN_ACCOUNT",
                        "platform": platform,
                        "broker": broker.capitalize(),
                        "login": login,
                        "password": pass_match.group(1),
                        "server": server_match.group(1),
                        "confidence": 0.95,
                        "reason": f"User wants to login to {broker} {platform} account",
                        "requires_confirmation": True,
                        "is_safe": True,
                        "risk_level": "MEDIUM",
                        "raw_user_input": user_message
                    }, ensure_ascii=False)
                else:
                    # Missing info
                    missing = []
                    if not pass_match:
                        missing.append("password")
                    if not server_match:
                        missing.append("server")

                    return json.dumps({
                        "action": "REQUEST_INFO",
                        "confidence": 1.0,
                        "reason": "Missing required information for login",
                        "requires_confirmation": False,
                        "is_safe": True,
                        "risk_level": "LOW",
                        "metadata": {
                            "missing_fields": missing,
                            "question": f"Vui lòng cung cấp thêm: {', '.join(missing)}"
                        },
                        "raw_user_input": user_message
                    }, ensure_ascii=False)

        elif any(word in user_lower for word in ['danh sách', 'list', 'xem tài khoản']):
            return json.dumps({
                "action": "LIST_ACCOUNTS",
                "confidence": 1.0,
                "reason": "User wants to view account list",
                "requires_confirmation": False,
                "is_safe": True,
                "risk_level": "LOW",
                "raw_user_input": user_message
            }, ensure_ascii=False)

        elif any(word in user_lower for word in ['quét', 'scan', 'terminal']):
            return json.dumps({
                "action": "SCAN_TERMINALS",
                "confidence": 1.0,
                "reason": "User wants to scan running terminals",
                "requires_confirmation": False,
                "is_safe": True,
                "risk_level": "LOW",
                "raw_user_input": user_message
            }, ensure_ascii=False)

        else:
            # Unknown command
            return json.dumps({
                "action": "REQUEST_INFO",
                "confidence": 0.5,
                "reason": "Could not understand user request",
                "requires_confirmation": False,
                "is_safe": True,
                "risk_level": "LOW",
                "metadata": {
                    "question": "Xin lỗi, tôi không hiểu yêu cầu của bạn. Bạn có thể nói rõ hơn không?\n\nVí dụ:\n- Đăng nhập tài khoản Exness MT5 login 12345678\n- Xem danh sách tài khoản\n- Quét terminal đang chạy"
                },
                "raw_user_input": user_message
            }, ensure_ascii=False)

    def _openai_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get response from OpenAI"""
        try:
            messages = [
                {"role": "system", "content": get_full_system_prompt()}
            ]

            # Add context if provided
            if context:
                context_msg = f"Context: {json.dumps(context, ensure_ascii=False)}"
                messages.append({"role": "system", "content": context_msg})

            # Add conversation history
            messages.extend(self.conversation_history)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            return json.dumps({
                "action": "REQUEST_INFO",
                "confidence": 0.0,
                "reason": f"AI Error: {str(e)}",
                "requires_confirmation": False,
                "is_safe": True,
                "risk_level": "LOW",
                "metadata": {"error": str(e)}
            })

    def _anthropic_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get response from Anthropic Claude"""
        try:
            system_prompt = get_full_system_prompt()
            if context:
                system_prompt += f"\n\nContext: {json.dumps(context, ensure_ascii=False)}"

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=self.conversation_history
            )

            return response.content[0].text

        except Exception as e:
            return json.dumps({
                "action": "REQUEST_INFO",
                "confidence": 0.0,
                "reason": f"AI Error: {str(e)}",
                "requires_confirmation": False,
                "is_safe": True,
                "risk_level": "LOW",
                "metadata": {"error": str(e)}
            })

    def _ollama_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get response from Ollama (local model)"""
        try:
            import requests

            system_prompt = get_full_system_prompt()
            if context:
                system_prompt += f"\n\nContext: {json.dumps(context, ensure_ascii=False)}"

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt}
                ] + self.conversation_history,
                "stream": False
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload
            )

            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                raise Exception(f"Ollama error: {response.status_code}")

        except Exception as e:
            return json.dumps({
                "action": "REQUEST_INFO",
                "confidence": 0.0,
                "reason": f"AI Error: {str(e)}",
                "requires_confirmation": False,
                "is_safe": True,
                "risk_level": "LOW",
                "metadata": {"error": str(e)}
            })

    def _parse_ai_response(self, ai_response: str, user_message: str) -> AIResponse:
        """
        Parse AI response to AIResponse object

        Args:
            ai_response: Raw AI response
            user_message: Original user message

        Returns:
            AIResponse object
        """
        # Try to extract JSON from response
        try:
            # Find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                json_str = json_match.group()
                command_dict = json.loads(json_str)

                # Create CommandSchema
                command = CommandSchema.from_dict(command_dict)

                # Determine response type
                if command.action == "REQUEST_INFO":
                    return AIResponse(
                        type="question",
                        content=command.metadata.get("question", "Cần thông tin thêm"),
                        command=command,
                        needs_more_info=True,
                        missing_fields=command.metadata.get("missing_fields", [])
                    )
                else:
                    return AIResponse(
                        type="command",
                        content=f"Command: {command.action}",
                        command=command,
                        needs_more_info=False
                    )

        except json.JSONDecodeError as e:
            # If can't parse JSON, treat as message
            return AIResponse(
                type="message",
                content=ai_response,
                needs_more_info=False
            )

        except Exception as e:
            # Error case
            return AIResponse(
                type="message",
                content=f"Lỗi khi phân tích phản hồi AI: {str(e)}",
                needs_more_info=False
            )

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []


# Test function
def test_ai_client():
    """Test AI client with mock provider"""
    print("=" * 80)
    print("TESTING AI CLIENT (MOCK MODE)")
    print("=" * 80)

    client = AIClient(provider="mock")

    # Test 1: Login with complete info
    print("\nTest 1: Login with complete info")
    print("-" * 80)
    response = client.send_message(
        "Đăng nhập tài khoản Exness MT5 login 12345678 pass Abc123 server Exness-MT5Live"
    )
    print(f"Type: {response.type}")
    print(f"Content: {response.content}")
    if response.command:
        print(f"Command: {response.command.to_json()}")

    # Test 2: Login with missing info
    print("\n\nTest 2: Login with missing info")
    print("-" * 80)
    client.reset_conversation()
    response = client.send_message("Login XM MT4 account 567890")
    print(f"Type: {response.type}")
    print(f"Content: {response.content}")
    if response.command:
        print(f"Command: {response.command.to_json()}")

    # Test 3: List accounts
    print("\n\nTest 3: List accounts")
    print("-" * 80)
    client.reset_conversation()
    response = client.send_message("Cho tôi xem danh sách tài khoản")
    print(f"Type: {response.type}")
    print(f"Content: {response.content}")
    if response.command:
        print(f"Command: {response.command.to_json()}")


if __name__ == "__main__":
    test_ai_client()
