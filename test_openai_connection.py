#!/usr/bin/env python3
"""
Test OpenAI API Connection
Quick test to verify API key and connectivity
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_openai():
    """Test OpenAI API connection"""
    print("=" * 80)
    print("Testing OpenAI API Connection")
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

        print(f"✓ Config loaded successfully")
        print(f"  AI Provider: {config.get('ai_provider')}")
        print()

    except Exception as e:
        print(f"✗ Error loading config: {str(e)}")
        return False

    # Get API key
    api_key = config.get("openai", {}).get("api_key")
    model = config.get("openai", {}).get("model", "gpt-3.5-turbo")

    if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
        print("✗ OpenAI API key not configured in config/ai_config.json")
        return False

    print(f"✓ API key found: {api_key[:20]}...{api_key[-10:]}")
    print(f"✓ Model: {model}")
    print()

    # Test connection
    try:
        print("Testing connection to OpenAI API...")
        print()

        import openai
        client = openai.OpenAI(api_key=api_key)

        # Simple test message
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond in Vietnamese."},
                {"role": "user", "content": "Chào bạn! Tôi đang test kết nối OpenAI API. Hãy trả lời ngắn gọn."}
            ],
            temperature=0.7,
            max_tokens=100
        )

        ai_message = response.choices[0].message.content

        print("✓ OpenAI API connection successful!")
        print()
        print("AI Response:")
        print("-" * 80)
        print(ai_message)
        print("-" * 80)
        print()
        print("=" * 80)
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)
        print()
        print("Your OpenAI integration is ready to use!")
        print()

        return True

    except Exception as e:
        print(f"✗ Error connecting to OpenAI: {str(e)}")
        print()
        print("Possible issues:")
        print("  1. Invalid API key")
        print("  2. No internet connection")
        print("  3. OpenAI API is down")
        print("  4. API key has no credits")
        print()
        return False


if __name__ == "__main__":
    success = test_openai()
    sys.exit(0 if success else 1)
