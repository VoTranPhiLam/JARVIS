#!/usr/bin/env python3
"""
JARVIS Chat Demo - Interactive CLI
Chat with OpenAI-powered AI without opening GUI
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_integration.ai_client import AIClient


def print_banner():
    """Print welcome banner"""
    print()
    print("=" * 80)
    print("⚡ JARVIS - MT4/MT5 AI Chat Demo ⚡")
    print("=" * 80)
    print()
    print("Chào mừng bạn đến với JARVIS Chat Demo!")
    print("Bạn có thể chat với AI để test tính năng trước khi mở GUI.")
    print()
    print("Lệnh đặc biệt:")
    print("  - Gõ 'exit' hoặc 'quit' để thoát")
    print("  - Gõ 'reset' để reset cuộc trò chuyện")
    print("  - Gõ 'help' để xem ví dụ lệnh")
    print()
    print("=" * 80)
    print()


def print_help():
    """Print help and examples"""
    print()
    print("📚 VÍ DỤ LỆNH:")
    print("-" * 80)
    print()
    print("1. Xem danh sách tài khoản:")
    print("   → Cho tôi xem danh sách tài khoản")
    print()
    print("2. Truy vấn thông tin:")
    print("   → Xem thông tin tài khoản Exness")
    print("   → Tài khoản nào có login 12345678?")
    print("   → Server của tài khoản XM là gì?")
    print()
    print("3. Đăng nhập:")
    print("   → Đăng nhập tài khoản Exness MT5 login 12345678 pass MyPass server Exness-MT5Live")
    print()
    print("4. Quét terminal:")
    print("   → Quét các terminal MT4/MT5 đang chạy")
    print()
    print("-" * 80)
    print()


def format_command(command_dict):
    """Format command JSON for display"""
    # Important fields
    action = command_dict.get('action', 'N/A')
    confidence = command_dict.get('confidence', 0)
    reason = command_dict.get('reason', 'N/A')
    risk_level = command_dict.get('risk_level', 'N/A')

    output = []
    output.append(f"📋 Command: {action}")
    output.append(f"   Confidence: {confidence:.2f}")
    output.append(f"   Risk Level: {risk_level}")
    output.append(f"   Reason: {reason}")

    # Show specific fields
    if command_dict.get('broker'):
        output.append(f"   Broker: {command_dict['broker']}")
    if command_dict.get('platform'):
        output.append(f"   Platform: {command_dict['platform']}")
    if command_dict.get('login'):
        output.append(f"   Login: {command_dict['login']}")
    if command_dict.get('server'):
        output.append(f"   Server: {command_dict['server']}")
    if command_dict.get('query'):
        output.append(f"   Query: {command_dict['query']}")

    return "\n".join(output)


def main():
    """Main interactive chat loop"""
    print_banner()

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
        print(f"❌ Error loading config: {str(e)}")
        return

    # Get AI settings
    ai_provider = config.get("ai_provider", "mock")
    api_key = None
    model = None

    if ai_provider == "openai":
        api_key = config.get("openai", {}).get("api_key")
        model = config.get("openai", {}).get("model", "gpt-3.5-turbo")

        if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
            print("⚠️  Warning: OpenAI API key not configured")
            print("   Switching to Mock mode...")
            print()
            ai_provider = "mock"

    # Initialize AI Client
    try:
        print(f"🤖 Initializing AI Client...")
        print(f"   Provider: {ai_provider}")
        if model:
            print(f"   Model: {model}")
        print()

        client = AIClient(
            provider=ai_provider,
            api_key=api_key,
            model=model
        )

        print("✅ AI Client ready!")
        print()

    except Exception as e:
        print(f"❌ Error initializing AI Client: {str(e)}")
        return

    # Chat loop
    print("💬 Bắt đầu chat (gõ 'help' để xem ví dụ, 'exit' để thoát):")
    print("-" * 80)
    print()

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print()
                print("👋 Tạm biệt! Chúc bạn sử dụng JARVIS hiệu quả!")
                print()
                break

            elif user_input.lower() == 'reset':
                client.reset_conversation()
                print()
                print("🔄 Đã reset cuộc trò chuyện")
                print()
                continue

            elif user_input.lower() == 'help':
                print_help()
                continue

            # Send to AI
            print()
            print("AI: Đang phân tích...")

            try:
                response = client.send_message(user_input)

                # Clear the "analyzing" message
                print("\r" + " " * 50 + "\r", end="")

                # Display response based on type
                if response.type == "question":
                    print(f"AI: {response.content}")

                elif response.type == "command":
                    print(f"AI: ✅ Đã phân tích xong! Đây là command:")
                    print()
                    if response.command:
                        print(format_command(response.command.to_dict()))
                    print()
                    print("💡 Tip: Để thực thi command này, hãy mở GUI bằng: python mt_login_gui.py")

                else:
                    print(f"AI: {response.content}")

                print()
                print("-" * 80)
                print()

            except Exception as e:
                print(f"\nAI: ❌ Lỗi: {str(e)}")
                print()
                print("-" * 80)
                print()

        except KeyboardInterrupt:
            print()
            print()
            print("👋 Tạm biệt!")
            print()
            break

        except Exception as e:
            print(f"Error: {str(e)}")
            print()


if __name__ == "__main__":
    main()
