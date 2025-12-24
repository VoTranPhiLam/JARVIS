"""
MT4/MT5 Executor for JARVIS

Executes commands on MT4/MT5 terminals.
Integrates with existing mt_login.py logic.
"""

import time
import pyperclip
import pyautogui
from pywinauto import Desktop, Application
from typing import Optional, Tuple, List, Dict, Any
import psutil

from ai_integration.command_schema import CommandSchema, CommandType


class MTExecutor:
    """
    Executor for MT4/MT5 commands

    This class wraps the existing mt_login.py functionality
    and provides a clean interface for command execution.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MT Executor

        Args:
            config: Configuration dict (speed settings, etc.)
        """
        self.config = config or {
            "speed_settings": {
                "focus_delay": 0.5,
                "key_delay": 0.1,
                "form_open_delay": 1.0,
                "field_delay": 0.2
            }
        }
        self.speed_settings = self.config["speed_settings"]

    def execute_command(self, command: CommandSchema) -> Tuple[bool, str]:
        """
        Execute a command

        Args:
            command: CommandSchema to execute

        Returns:
            (success, message)
        """
        try:
            action = command.action

            if action == CommandType.LOGIN_ACCOUNT.value:
                return self.login_account(command)

            elif action == CommandType.SCAN_TERMINALS.value:
                return self.scan_terminals()

            elif action == CommandType.LIST_ACCOUNTS.value:
                return True, "LIST_ACCOUNTS should be handled by GUI"

            elif action == CommandType.CHECK_STATUS.value:
                return self.check_status()

            else:
                return False, f"Unknown command: {action}"

        except Exception as e:
            return False, f"Execution error: {str(e)}"

    def login_account(self, command: CommandSchema) -> Tuple[bool, str]:
        """
        Login to MT4/MT5 account

        Args:
            command: LOGIN_ACCOUNT command

        Returns:
            (success, message)
        """
        try:
            # Extract info from command
            platform_type = command.platform
            broker_keyword = command.broker
            login_id = command.login
            password = command.password
            server_name = command.server

            print(f"\n🚀 EXECUTING LOGIN COMMAND")
            print("=" * 60)
            print(f"Platform: {platform_type}")
            print(f"Broker: {broker_keyword}")
            print(f"Login: {login_id}")
            print(f"Server: {server_name}")
            print("=" * 60)

            # Step 1: Check platform compatibility
            mt_terminals = self.get_all_running_mt_terminals()
            compatible, error_msg = self._check_platform_compatibility(
                mt_terminals, platform_type
            )

            if not compatible:
                return False, error_msg

            # Step 2: Find target window
            target_win = self._find_mt_window(broker_keyword)
            if not target_win:
                return False, f"Không tìm thấy cửa sổ MT4/MT5 chứa: {broker_keyword}"

            print(f"✅ Tìm thấy cửa sổ: {target_win.window_text()}")

            # Step 3: Execute login
            success = self._execute_login_ui(
                target_win, login_id, password, server_name
            )

            if success:
                return True, f"Đã gửi yêu cầu đăng nhập tài khoản {login_id}"
            else:
                return False, "Lỗi khi thực hiện đăng nhập"

        except Exception as e:
            return False, f"Login error: {str(e)}"

        finally:
            # Always clear clipboard
            self._clear_clipboard()

    def scan_terminals(self) -> Tuple[bool, str]:
        """
        Scan running MT4/MT5 terminals

        Returns:
            (success, message with terminal list)
        """
        try:
            terminals = self.get_all_running_mt_terminals()

            if not terminals:
                return True, "Không tìm thấy terminal MT4/MT5 nào đang chạy"

            result = f"Tìm thấy {len(terminals)} terminal(s):\n"
            for i, term in enumerate(terminals, 1):
                result += f"{i}. {term['title']} ({term['platform']})\n"

            return True, result

        except Exception as e:
            return False, f"Scan error: {str(e)}"

    def check_status(self) -> Tuple[bool, str]:
        """
        Check system status

        Returns:
            (success, status message)
        """
        try:
            terminals = self.get_all_running_mt_terminals()
            status = f"Status: OK\n"
            status += f"Running terminals: {len(terminals)}\n"
            return True, status
        except Exception as e:
            return False, f"Status check error: {str(e)}"

    def get_all_running_mt_terminals(self) -> List[Dict[str, Any]]:
        """
        Find all running MT4/MT5 terminals

        Returns:
            List of terminal info dicts
        """
        windows = Desktop(backend="win32").windows()
        mt_terminals = []

        print("🔍 Scanning for MT4/MT5 terminals...")
        for win in windows:
            try:
                title = win.window_text()
                if not title:
                    continue

                title_lower = title.lower()
                mt_keywords = ["metatrader", "mt4", "mt5"]

                if any(keyword in title_lower for keyword in mt_keywords):
                    platform_type = self._detect_platform_type(win)
                    mt_terminals.append({
                        "window": win,
                        "title": title,
                        "platform": platform_type
                    })
                    print(f"  ✓ {title} ({platform_type})")

            except Exception as e:
                print(f"  ✗ Error: {str(e)}")

        return mt_terminals

    def _detect_platform_type(self, window_obj) -> str:
        """
        Detect platform type (MT4 or MT5)

        Args:
            window_obj: Window object from pywinauto

        Returns:
            "MT4" or "MT5"
        """
        try:
            # Get process ID
            process_id = window_obj.process_id()

            # Check process name
            all_processes = {
                proc.pid: proc.name()
                for proc in psutil.process_iter(['pid', 'name'])
            }

            if process_id in all_processes:
                process_name = all_processes[process_id].lower()

                if "terminal64" in process_name:
                    return "MT5"
                elif "terminal" in process_name:
                    return "MT4"

            # Fallback to window title
            window_title = window_obj.window_text().lower()
            if "mt5" in window_title or "metatrader 5" in window_title:
                return "MT5"
            elif "mt4" in window_title or "metatrader 4" in window_title:
                return "MT4"

            # Default to MT4
            return "MT4"

        except Exception as e:
            print(f"Detection error: {str(e)}")
            return "MT4"

    def _check_platform_compatibility(
        self,
        mt_terminals: List[Dict[str, Any]],
        target_platform_type: str
    ) -> Tuple[bool, str]:
        """
        Check platform compatibility

        Returns:
            (is_compatible, error_message)
        """
        if not mt_terminals:
            return True, ""

        running_platforms = set([t["platform"] for t in mt_terminals])

        if len(running_platforms) == 1:
            running_platform = list(running_platforms)[0]
            if running_platform != target_platform_type:
                error_msg = (
                    f"⚠️ Không thể đăng nhập tài khoản {target_platform_type} "
                    f"khi đang có {running_platform} đang chạy"
                )
                return False, error_msg

        return True, ""

    def _find_mt_window(self, broker_keyword: str):
        """
        Find MT4/MT5 window by broker keyword

        Args:
            broker_keyword: Broker name to search for

        Returns:
            Window object or None
        """
        windows = Desktop(backend="win32").windows()

        for win in windows:
            try:
                title = win.window_text()
                if broker_keyword.lower() in title.lower():
                    return win
            except:
                continue

        return None

    def _execute_login_ui(
        self,
        target_win,
        login_id: str,
        password: str,
        server_name: str
    ) -> bool:
        """
        Execute login UI automation

        Args:
            target_win: Target window
            login_id: Login ID
            password: Password
            server_name: Server name

        Returns:
            True if successful
        """
        try:
            # Connect to window
            app = Application(backend="win32").connect(handle=target_win.handle)
            main_win = app.window(handle=target_win.handle)
            main_win.set_focus()
            time.sleep(self.speed_settings["focus_delay"])

            # Open login form (Alt+F → L)
            pyautogui.hotkey('alt', 'f')
            time.sleep(self.speed_settings["key_delay"])
            pyautogui.press('l')
            time.sleep(self.speed_settings["form_open_delay"])

            print("✅ Opened login form")

            # Fill login form
            print("📝 Filling login form...")

            # Login ID
            pyperclip.copy(login_id)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(self.speed_settings["field_delay"])
            pyautogui.press('tab')
            time.sleep(self.speed_settings["field_delay"])

            # Password
            pyperclip.copy(password)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(self.speed_settings["field_delay"])
            pyautogui.press('tab')
            time.sleep(self.speed_settings["field_delay"])

            # Server
            pyperclip.copy(server_name)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(self.speed_settings["field_delay"])

            # Submit (Tab twice → Enter)
            pyautogui.press('tab')
            time.sleep(self.speed_settings["key_delay"])
            pyautogui.press('tab')
            time.sleep(self.speed_settings["key_delay"])
            pyautogui.press('enter')

            print("✅ Login form submitted")
            return True

        except Exception as e:
            print(f"❌ UI automation error: {str(e)}")
            return False

    def _clear_clipboard(self):
        """Clear clipboard"""
        try:
            pyperclip.copy('')
        except:
            pass


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("MT EXECUTOR TEST")
    print("=" * 80)

    executor = MTExecutor()

    # Test scan
    print("\nTest: Scan terminals")
    success, message = executor.scan_terminals()
    print(f"Success: {success}")
    print(f"Message: {message}")
