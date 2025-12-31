#!/usr/bin/env python3
"""
Test JARVIS AI Client with Real OpenAI
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_integration.ai_client import AIClient


def test_jarvis_ai():
    """Test JARVIS AI Client with OpenAI"""
    print("=" * 80)
    print("Testing JARVIS AI Client with OpenAI")
    print("=" * 80)
    print()

    # Load config
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config",
            "ai_config.json"
        )

        with open(config_path, 'r') as f:
            config = json.load(f)

    except Exception as e:
        print(f"✗ Error loading config: {str(e)}")
        return False

    # Get OpenAI settings
    api_key = config.get("openai", {}).get("api_key")
    model = config.get("openai", {}).get("model", "gpt-3.5-turbo")

    # Initialize AI Client
    try:
        print(f"Initializing AI Client...")
        print(f"  Provider: openai")
        print(f"  Model: {model}")
        print()

        client = AIClient(
            provider="openai",
            api_key=api_key,
            model=model
        )

        print("✓ AI Client initialized successfully")
        print()

    except Exception as e:
        print(f"✗ Error initializing AI Client: {str(e)}")
        return False

    # Test various commands
    test_messages = [
        "Cho tôi xem danh sách tài khoản",
        "Xem thông tin tài khoản Exness",
        "Đăng nhập tài khoản Exness MT5 login 12345678",
        "Quét terminal đang chạy"
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")
        print("-" * 80)

        try:
            response = client.send_message(message)

            print(f"Response Type: {response.type}")
            print(f"Content: {response.content}")

            if response.command:
                print(f"\nCommand JSON:")
                print(json.dumps(response.command.to_dict(), indent=2, ensure_ascii=False))

            print()

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            print()

        # Reset conversation for next test
        client.reset_conversation()

    print("=" * 80)
    print("✓ ALL TESTS COMPLETED!")
    print("=" * 80)
    print()

    return True


if __name__ == "__main__":
    success = test_jarvis_ai()
    sys.exit(0 if success else 1)
