#!/usr/bin/env python3
"""
JARVIS - MT4/MT5 AI Automation System
Main Entry Point

Author: JARVIS Team
Version: 1.0.0
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def load_config():
    """Load configuration from file"""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config",
        "ai_config.json"
    )

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config: {str(e)}")
        return {"ai_provider": "mock"}


def main():
    """Main application entry point"""
    print("=" * 80)
    print("⚡ JARVIS - MT4/MT5 AI Automation System ⚡")
    print("=" * 80)
    print()

    # Load configuration
    config = load_config()
    ai_provider = config.get("ai_provider", "mock")

    print(f"AI Provider: {ai_provider}")
    print()

    # Get API key if needed
    api_key = None
    if ai_provider == "openai":
        api_key = config.get("openai", {}).get("api_key")
        if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
            print("⚠️  Warning: OpenAI API key not configured")
            print("   Using mock mode instead")
            ai_provider = "mock"
    elif ai_provider == "anthropic":
        api_key = config.get("anthropic", {}).get("api_key")
        if not api_key or api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
            print("⚠️  Warning: Anthropic API key not configured")
            print("   Using mock mode instead")
            ai_provider = "mock"

    # Create Qt Application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look

    # Create main window
    window = MainWindow(ai_provider=ai_provider, api_key=api_key)
    window.show()

    print("✅ Application started successfully")
    print("=" * 80)
    print()

    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
