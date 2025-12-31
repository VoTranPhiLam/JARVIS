"""
Main Window for JARVIS MT4/MT5 AI Automation

Integrates all components:
- Account table
- AI chat widget
- MT executor
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QSplitter, QLabel, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Optional

from gui.chat_widget import ChatWidget
from core.mt_executor import MTExecutor
from core.account_manager import AccountManager, Account
from ai_integration.ai_client import AIClient
from ai_integration.command_schema import CommandSchema, CommandType


class ExecutorThread(QThread):
    """Thread for executing MT commands (non-blocking)"""
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, executor: MTExecutor, command: CommandSchema):
        super().__init__()
        self.executor = executor
        self.command = command

    def run(self):
        """Execute command in background"""
        success, message = self.executor.execute_command(self.command)
        self.finished.emit(success, message)


class MainWindow(QMainWindow):
    """
    Main application window

    Layout:
    ┌─────────────────────────────────┐
    │         JARVIS Title            │
    ├──────────────┬──────────────────┤
    │              │                  │
    │   Account    │   AI Chat        │
    │   Table      │   Widget         │
    │              │                  │
    │              │                  │
    └──────────────┴──────────────────┘
    """

    def __init__(
        self,
        ai_provider: str = "mock",
        api_key: Optional[str] = None
    ):
        super().__init__()

        # Initialize components
        self.account_manager = AccountManager()
        self.mt_executor = MTExecutor()
        self.ai_client = AIClient(provider=ai_provider, api_key=api_key)

        # Setup UI
        self._setup_ui()
        self._setup_connections()
        self._load_accounts()

    def _setup_ui(self):
        """Setup main UI"""
        self.setWindowTitle("JARVIS - MT4/MT5 AI Automation")
        self.setGeometry(100, 100, 1400, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # === HEADER ===
        header = QLabel("⚡ JARVIS - MT4/MT5 AI Automation System ⚡")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db
                );
                color: white;
                padding: 15px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(header)

        # === MAIN CONTENT SPLITTER ===
        splitter = QSplitter(Qt.Horizontal)

        # LEFT PANEL: Account Management
        left_panel = self._create_account_panel()
        splitter.addWidget(left_panel)

        # RIGHT PANEL: AI Chat
        self.chat_widget = ChatWidget(ai_client=self.ai_client)
        splitter.addWidget(self.chat_widget)

        # Set splitter ratios
        splitter.setStretchFactor(0, 1)  # Account panel
        splitter.setStretchFactor(1, 1)  # Chat panel

        layout.addWidget(splitter)

        # === STATUS BAR ===
        self.statusBar().showMessage("Ready")

    def _create_account_panel(self) -> QWidget:
        """Create account management panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Panel header
        header = QLabel("📊 Account Management")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 5px;")
        layout.addWidget(header)

        # Account table
        self.account_table = QTableWidget()
        self.account_table.setColumnCount(5)
        self.account_table.setHorizontalHeaderLabels([
            "Broker", "Platform", "Login", "Server", "Status"
        ])

        # Table styling
        self.account_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)

        # Auto-resize columns
        header = self.account_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.account_table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.scan_btn = QPushButton("🔍 Scan Terminals")
        self.scan_btn.setStyleSheet(self._button_style("#3498db"))
        button_layout.addWidget(self.scan_btn)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet(self._button_style("#27ae60"))
        button_layout.addWidget(self.refresh_btn)

        layout.addLayout(button_layout)

        return panel

    def _button_style(self, color: str) -> str:
        """Generate button style"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
        """

    def _setup_connections(self):
        """Setup signal/slot connections"""
        # Chat widget signals
        self.chat_widget.execute_command.connect(self._on_execute_command)

        # Button signals
        self.scan_btn.clicked.connect(self._on_scan_terminals)
        self.refresh_btn.clicked.connect(self._load_accounts)

    def _load_accounts(self):
        """Load accounts into table"""
        self.account_table.setRowCount(0)
        accounts = self.account_manager.get_all_accounts()

        for acc in accounts:
            row = self.account_table.rowCount()
            self.account_table.insertRow(row)

            self.account_table.setItem(row, 0, QTableWidgetItem(acc.broker))
            self.account_table.setItem(row, 1, QTableWidgetItem(acc.platform))
            self.account_table.setItem(row, 2, QTableWidgetItem(acc.login))
            self.account_table.setItem(row, 3, QTableWidgetItem(acc.server))
            self.account_table.setItem(row, 4, QTableWidgetItem(acc.status))

        self.statusBar().showMessage(f"Loaded {len(accounts)} accounts")

    def _on_scan_terminals(self):
        """Handle scan terminals button"""
        self.statusBar().showMessage("Scanning terminals...")
        success, message = self.mt_executor.scan_terminals()

        if success:
            QMessageBox.information(self, "Scan Results", message)
            self.statusBar().showMessage("Scan completed")
        else:
            QMessageBox.warning(self, "Scan Error", message)
            self.statusBar().showMessage("Scan failed")

    def _handle_query_account(self, command: CommandSchema):
        """
        Handle QUERY_ACCOUNT command

        Args:
            command: QUERY_ACCOUNT command
        """
        try:
            # Query accounts từ AccountManager
            accounts = self.account_manager.search_accounts(
                query=command.query,
                broker=command.broker,
                login=command.login,
                platform=command.platform
            )

            if not accounts:
                self.chat_widget.add_execution_result(
                    True,
                    "Không tìm thấy tài khoản nào phù hợp với yêu cầu."
                )
                return

            # Format results
            result_text = f"📋 Tìm thấy {len(accounts)} tài khoản:\n\n"
            for i, acc in enumerate(accounts, 1):
                result_text += f"{i}. {acc.broker} - Login: {acc.login}\n"
                result_text += f"   Platform: {acc.platform}\n"
                result_text += f"   Server: {acc.server}\n"
                if acc.name:
                    result_text += f"   Name: {acc.name}\n"
                result_text += f"   Status: {acc.status}\n\n"

            # Display results in chat
            self.chat_widget.add_execution_result(True, result_text)

            # Update status bar
            self.statusBar().showMessage(f"✅ Query completed: {len(accounts)} account(s) found")

        except Exception as e:
            self.chat_widget.add_execution_result(
                False,
                f"Lỗi khi query accounts: {str(e)}"
            )
            self.statusBar().showMessage(f"❌ Query failed: {str(e)}")

    def _on_execute_command(self, command: CommandSchema):
        """
        Handle command execution from chat widget

        Args:
            command: CommandSchema to execute
        """
        # Handle QUERY_ACCOUNT directly (no need for MT executor)
        if command.action == CommandType.QUERY_ACCOUNT.value:
            self._handle_query_account(command)
            return

        # Confirmation dialog for risky commands
        if command.requires_confirmation:
            reply = QMessageBox.question(
                self,
                "Confirm Execution",
                f"Execute command: {command.action}?\n\n"
                f"Platform: {command.platform}\n"
                f"Broker: {command.broker}\n"
                f"Login: {command.login}\n"
                f"Server: {command.server}\n\n"
                f"Risk Level: {command.risk_level}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                self.chat_widget.add_execution_result(
                    False, "User cancelled execution"
                )
                return

        # Execute in background thread
        self.statusBar().showMessage(f"Executing: {command.action}...")

        self.executor_thread = ExecutorThread(self.mt_executor, command)
        self.executor_thread.finished.connect(self._on_execution_finished)
        self.executor_thread.start()

    def _on_execution_finished(self, success: bool, message: str):
        """Handle execution completion"""
        self.chat_widget.add_execution_result(success, message)

        if success:
            self.statusBar().showMessage(f"✅ {message}")

            # If LOGIN command, save account
            if self.executor_thread.command.action == CommandType.LOGIN_ACCOUNT.value:
                self._save_account_from_command(self.executor_thread.command)

            # Refresh account list
            self._load_accounts()
        else:
            self.statusBar().showMessage(f"❌ {message}")

    def _save_account_from_command(self, command: CommandSchema):
        """Save account from login command"""
        try:
            account = Account(
                login=command.login,
                broker=command.broker,
                platform=command.platform,
                server=command.server,
                password=command.password,
                status="active"
            )

            self.account_manager.add_account(account)
        except Exception as e:
            print(f"Error saving account: {str(e)}")

    def closeEvent(self, event):
        """Handle window close"""
        # Save accounts on exit
        self.account_manager.save_accounts()
        event.accept()


# Main entry point
def main():
    """Main function to run the application"""
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create main window
    # For production, use: MainWindow(ai_provider="openai", api_key="your-key")
    window = MainWindow(ai_provider="mock")
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
