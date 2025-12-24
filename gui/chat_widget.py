"""
Chat Widget for JARVIS AI Integration

PyQt5 chat interface with AI command preview
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QFrame, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QTextCursor, QFont, QColor
import json
from datetime import datetime
from typing import Optional

from ai_integration.ai_client import AIClient
from ai_integration.command_validator import CommandValidator
from ai_integration.command_schema import CommandSchema, AIResponse


class AIWorker(QThread):
    """Worker thread for AI processing (non-blocking UI)"""
    finished = pyqtSignal(object)  # AIResponse
    error = pyqtSignal(str)

    def __init__(self, ai_client: AIClient, message: str, context: Optional[dict] = None):
        super().__init__()
        self.ai_client = ai_client
        self.message = message
        self.context = context

    def run(self):
        """Run AI processing in background"""
        try:
            response = self.ai_client.send_message(self.message, self.context)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class ChatWidget(QWidget):
    """
    AI Chat Widget

    Features:
    - Chat history display
    - User input field
    - Send button
    - Command preview panel
    - Execute button
    """

    # Signals
    command_received = pyqtSignal(object)  # CommandSchema
    execute_command = pyqtSignal(object)  # CommandSchema

    def __init__(
        self,
        ai_client: Optional[AIClient] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.ai_client = ai_client or AIClient(provider="mock")
        self.validator = CommandValidator(strict_mode=True)
        self.current_command: Optional[CommandSchema] = None
        self.ai_worker: Optional[AIWorker] = None

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)

        # === HEADER ===
        header = QLabel("🤖 JARVIS AI Assistant")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("background-color: #2c3e50; color: white; padding: 10px;")
        layout.addWidget(header)

        # === SPLITTER for chat and command preview ===
        splitter = QSplitter(Qt.Vertical)

        # === CHAT DISPLAY ===
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        splitter.addWidget(self.chat_display)

        # === COMMAND PREVIEW PANEL ===
        command_frame = QFrame()
        command_frame.setFrameStyle(QFrame.StyledPanel)
        command_layout = QVBoxLayout(command_frame)

        command_header = QLabel("📋 AI Command Preview")
        command_header.setFont(QFont("Arial", 11, QFont.Bold))
        command_header.setStyleSheet("color: #2980b9;")
        command_layout.addWidget(command_header)

        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setFont(QFont("Consolas", 9))
        self.command_preview.setMaximumHeight(200)
        self.command_preview.setStyleSheet("""
            QTextEdit {
                background-color: #fef9e7;
                border: 1px solid #f39c12;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        command_layout.addWidget(self.command_preview)

        # Execute button
        self.execute_btn = QPushButton("▶ Execute Command")
        self.execute_btn.setEnabled(False)
        self.execute_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        command_layout.addWidget(self.execute_btn)

        splitter.addWidget(command_frame)
        splitter.setStretchFactor(0, 3)  # Chat takes more space
        splitter.setStretchFactor(1, 1)  # Command preview smaller

        layout.addWidget(splitter)

        # === INPUT AREA ===
        input_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Nhập lệnh tại đây... (ví dụ: Đăng nhập tài khoản Exness MT5 login 12345678)")
        self.input_field.setFont(QFont("Arial", 10))
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        input_layout.addWidget(self.input_field)

        self.send_btn = QPushButton("📤 Send")
        self.send_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        # Welcome message
        self._add_system_message("Xin chào! Tôi là JARVIS, trợ lý AI của bạn. Tôi có thể giúp bạn quản lý tài khoản MT4/MT5.\n\nVí dụ lệnh:\n- Đăng nhập tài khoản Exness MT5 login 12345678\n- Xem danh sách tài khoản\n- Quét terminal đang chạy")

    def _setup_connections(self):
        """Setup signal/slot connections"""
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.input_field.returnPressed.connect(self._on_send_clicked)
        self.execute_btn.clicked.connect(self._on_execute_clicked)

    def _on_send_clicked(self):
        """Handle send button click"""
        message = self.input_field.text().strip()
        if not message:
            return

        # Clear input
        self.input_field.clear()

        # Add user message to chat
        self._add_user_message(message)

        # Disable send button while processing
        self.send_btn.setEnabled(False)
        self.send_btn.setText("⏳ Processing...")

        # Process with AI in background thread
        self.ai_worker = AIWorker(self.ai_client, message)
        self.ai_worker.finished.connect(self._on_ai_response)
        self.ai_worker.error.connect(self._on_ai_error)
        self.ai_worker.start()

    def _on_ai_response(self, response: AIResponse):
        """Handle AI response"""
        # Re-enable send button
        self.send_btn.setEnabled(True)
        self.send_btn.setText("📤 Send")

        # Handle different response types
        if response.type == "question":
            # AI needs more info
            self._add_ai_message(response.content)
            self.command_preview.setPlainText("⚠️ Thiếu thông tin, vui lòng cung cấp thêm")
            self.execute_btn.setEnabled(False)

        elif response.type == "command":
            # AI returned a command
            if response.command:
                # Validate command
                is_valid, error_msg = self.validator.validate(response.command)

                if is_valid:
                    self._add_ai_message(f"✅ Command hợp lệ: {response.command.action}")
                    self._display_command(response.command)
                    self.current_command = response.command
                    self.execute_btn.setEnabled(True)
                    self.command_received.emit(response.command)
                else:
                    self._add_ai_message(f"❌ Command không hợp lệ: {error_msg}")
                    self.command_preview.setPlainText(f"❌ Lỗi: {error_msg}")
                    self.execute_btn.setEnabled(False)

        elif response.type == "message":
            # AI sent a text message
            self._add_ai_message(response.content)
            self.command_preview.setPlainText("💬 Không có command")
            self.execute_btn.setEnabled(False)

    def _on_ai_error(self, error: str):
        """Handle AI error"""
        self.send_btn.setEnabled(True)
        self.send_btn.setText("📤 Send")
        self._add_system_message(f"❌ Lỗi AI: {error}")

    def _on_execute_clicked(self):
        """Handle execute button click"""
        if self.current_command:
            self.execute_command.emit(self.current_command)
            self._add_system_message(f"🚀 Đang thực thi command: {self.current_command.action}")
            self.execute_btn.setEnabled(False)

    def _add_user_message(self, message: str):
        """Add user message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.append(f'<div style="color: #2c3e50; margin: 5px 0;">'
                                 f'<b>[{timestamp}] 👤 You:</b> {message}'
                                 f'</div>')
        self._scroll_to_bottom()

    def _add_ai_message(self, message: str):
        """Add AI message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.append(f'<div style="color: #2980b9; margin: 5px 0;">'
                                 f'<b>[{timestamp}] 🤖 JARVIS:</b> {message}'
                                 f'</div>')
        self._scroll_to_bottom()

    def _add_system_message(self, message: str):
        """Add system message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.append(f'<div style="color: #7f8c8d; margin: 5px 0; font-style: italic;">'
                                 f'<b>[{timestamp}] ℹ️ System:</b> {message}'
                                 f'</div>')
        self._scroll_to_bottom()

    def _display_command(self, command: CommandSchema):
        """Display command in preview panel"""
        command_json = command.to_json()
        self.command_preview.setPlainText(command_json)

    def _scroll_to_bottom(self):
        """Scroll chat display to bottom"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)

    def add_execution_result(self, success: bool, message: str):
        """Add execution result to chat"""
        if success:
            self._add_system_message(f"✅ Thực thi thành công: {message}")
        else:
            self._add_system_message(f"❌ Thực thi thất bại: {message}")

        # Clear current command
        self.current_command = None
        self.command_preview.setPlainText("Chưa có command")

    def set_context(self, context: dict):
        """Set context for AI (e.g., account list)"""
        # This can be used to provide current accounts to AI
        pass


# Test the widget standalone
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create chat widget with mock AI
    chat = ChatWidget()
    chat.setWindowTitle("JARVIS AI Chat - Test")
    chat.resize(800, 600)
    chat.show()

    sys.exit(app.exec_())
