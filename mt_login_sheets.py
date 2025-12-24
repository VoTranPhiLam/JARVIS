import sys
import json
import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QFileDialog,
    QMessageBox, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QInputDialog, QCheckBox, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon
import pyperclip
import time
import re
import pyautogui
import subprocess
import psutil
import win32process
import win32gui
import win32con
from functools import partial

# Khởi tạo COM ở đầu chương trình
try:
    import pythoncom
    pythoncom.CoInitialize()
    print("COM initialization successful")
except ImportError:
    print("Warning: Không thể import pythoncom")
except Exception as com_err:
    print(f"Warning: Không thể khởi tạo COM: {str(com_err)}")

# Import pywinauto sau khi khởi tạo COM
try:
    from pywinauto import Desktop, Application
except ImportError as e:
    print(f"Warning: Không thể import pywinauto: {str(e)}")
except Exception as e:
    print(f"Warning: Lỗi khi import pywinauto: {str(e)}")

class GoogleSheetMT4Login(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MT4/MT5 Login - Google Sheets")
        
        # Hiển thị cửa sổ chính ở chế độ toàn màn hình
        screen_rect = QApplication.desktop().availableGeometry()
        self.setGeometry(0, 0, screen_rect.width(), screen_rect.height())
        
        # Biến lưu trữ dữ liệu
        self.credentials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
        import sys
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(app_dir, "config.json")
        self.sheet_data = None
        self.worksheet = None
        self.df = None
        self.all_data = None  # Lưu toàn bộ dữ liệu
        self.column_map = {}  # Ánh xạ các cột Excel (A, B, C...) sang index (0, 1, 2...)
        self.original_df = None  # Lưu DataFrame gốc trước khi lọc
        
        # Tạo ánh xạ các cột
        for i in range(26):  # A-Z
            self.column_map[chr(65 + i)] = i
        
        # Setup UI
        self.setup_ui()
        
        # Tải cấu hình đã lưu nếu có
        self.load_config()
    
    def setup_ui(self):
        # Widget chính
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        # Tab chính (dữ liệu tài khoản, quét, console)
        self.main_tab = QWidget()
        self.tab_widget.addTab(self.main_tab, "Quản lý tài khoản")
        main_tab_layout = QVBoxLayout()
        self.main_tab.setLayout(main_tab_layout)
        
        # Top bar với nút kết nối và cài đặt
        top_bar = QHBoxLayout()
        connect_btn = QPushButton("Kết nối và Lấy dữ liệu")
        connect_btn.clicked.connect(self.connect_to_sheet)
        connect_btn.setStyleSheet("font-weight: bold; font-size: 12px; padding: 8px;")
        top_bar.addWidget(connect_btn)
        branch_check_btn = QPushButton("Kiểm tra đúng nhánh")
        branch_check_btn.clicked.connect(self.check_branch_accounts)
        branch_check_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; font-size: 12px; padding: 8px;")
        top_bar.addWidget(branch_check_btn)
        # ĐÃ XOÁ combobox lọc nhánh và thanh tìm kiếm sàn
        top_bar.addStretch()
        # Di chuyển nút quét các sàn trên máy sang cạnh nút kiểm tra tài khoản hết tiền
        check_low_equity_btn = QPushButton("Kiểm tra tài khoản hết tiền")
        check_low_equity_btn.setStyleSheet("background-color: #E53935; color: white; font-weight: bold; font-size: 12px; padding: 8px;")
        check_low_equity_btn.clicked.connect(self.check_low_equity_accounts)
        scan_btn = QPushButton("Quét các sàn trên máy")
        scan_btn.setStyleSheet("background-color: #FFC107; color: black; font-weight: bold; font-size: 12px; padding: 8px;")
        scan_btn.clicked.connect(self.scan_all_accounts)
        top_bar.addWidget(check_low_equity_btn)
        top_bar.addWidget(scan_btn)
        settings_btn = QPushButton("Cài đặt")
        settings_btn.clicked.connect(self.open_settings)
        settings_btn.setStyleSheet("padding: 5px 10px;")
        top_bar.addWidget(settings_btn)
        main_tab_layout.addLayout(top_bar)
        # --- Thanh tìm kiếm mới ---
        search_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm theo Tên sàn hoặc Login ID...")
        self.search_input.textChanged.connect(self.search_accounts)  # Tìm kiếm tự động khi gõ
        search_btn = QPushButton("Tìm kiếm")
        search_btn.setStyleSheet("padding: 5px 10px;")
        search_btn.clicked.connect(self.search_accounts)
        clear_search_btn = QPushButton("Xóa tìm kiếm")
        clear_search_btn.setStyleSheet("padding: 5px 10px;")
        clear_search_btn.clicked.connect(self.clear_search)
        search_bar_layout.addWidget(QLabel("🔍 Tìm kiếm:"))
        search_bar_layout.addWidget(self.search_input)
        search_bar_layout.addWidget(search_btn)
        search_bar_layout.addWidget(clear_search_btn)
        search_bar_layout.addStretch()
        main_tab_layout.addLayout(search_bar_layout)
        # --- End thanh tìm kiếm ---
        
        # Group Box cho Data Display
        data_group = QGroupBox("Dữ liệu tài khoản")
        data_layout = QVBoxLayout()
        data_group.setLayout(data_layout)
        self.data_table = QTableWidget()
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        data_layout.addWidget(self.data_table)
        login_btn = QPushButton("Đăng nhập vào tài khoản đã chọn")
        login_btn.clicked.connect(self.login_to_mt)
        login_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 12px; padding: 8px;")
        data_layout.addWidget(login_btn)
        main_tab_layout.addWidget(data_group)
        scan_group = QGroupBox("Kết quả quét các sàn trên máy")
        scan_layout = QVBoxLayout()
        scan_group.setLayout(scan_layout)
        self.scan_result_table = QTableWidget()
        self.scan_result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.scan_result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.scan_result_table.setAlternatingRowColors(True)
        self.scan_result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scan_result_table.setVisible(False)
        scan_layout.addWidget(self.scan_result_table)
        main_tab_layout.addWidget(scan_group)
        console_group = QGroupBox("Console")
        console_layout = QVBoxLayout()
        console_group.setLayout(console_layout)
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        console_layout.addWidget(self.data_display)
        main_tab_layout.addWidget(console_group)
        # Ẩn các widget input từ giao diện chính
        self.sheet_url_input = QLineEdit()
        self.worksheet_input = QLineEdit()
        self.worksheet_input.setText("Sheet1")
        self.header_row_input = QLineEdit()
        self.header_row_input.setText("1")
        self.broker_col_input = QLineEdit()
        self.broker_col_input.setText("F")
        self.server_col_input = QLineEdit()
        self.server_col_input.setText("D")
        self.login_col_input = QLineEdit()
        self.login_col_input.setText("G")
        self.pass_col_input = QLineEdit()
        self.pass_col_input.setText("I")
        self.branch_col_input = QLineEdit()
        self.branch_col_input.setText("E")
        self.column_combo = QComboBox()
        
        # Tab hiển thị tài khoản hết tiền
        # ĐÃ XOÁ TOÀN BỘ PHẦN TẠO TAB self.low_equity_tab
        # ... existing code ...
    
    def open_settings(self):
        """Mở dialog cài đặt"""
        dialog = SettingsDialog(self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self.data_display.setText("✅ Đã lưu cài đặt thành công!")
    
    def save_config(self):
        """Lưu cấu hình hiện tại vào file config.json"""
        try:
            config = {
                "sheet_url": self.sheet_url_input.text(),
                "worksheet": self.worksheet_input.text(),
                "header_row": self.header_row_input.text(),
                "broker_col": self.broker_col_input.text(),
                "server_col": self.server_col_input.text(),
                "login_col": self.login_col_input.text(),
                "pass_col": self.pass_col_input.text(),
                "branch_col": self.branch_col_input.text()
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            QMessageBox.information(self, "Thành công", "Đã lưu cấu hình thành công!")
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu cấu hình: {str(e)}")
    
    def load_config(self):
        """Tải cấu hình từ file config.json nếu có"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Điền thông tin vào form
                if "sheet_url" in config and config["sheet_url"]:
                    self.sheet_url_input.setText(config["sheet_url"])
                    
                if "worksheet" in config and config["worksheet"]:
                    self.worksheet_input.setText(config["worksheet"])
                    
                if "header_row" in config and config["header_row"]:
                    self.header_row_input.setText(config["header_row"])
                    
                if "broker_col" in config and config["broker_col"]:
                    self.broker_col_input.setText(config["broker_col"])
                    
                if "server_col" in config and config["server_col"]:
                    self.server_col_input.setText(config["server_col"])
                    
                if "login_col" in config and config["login_col"]:
                    self.login_col_input.setText(config["login_col"])
                    
                if "pass_col" in config and config["pass_col"]:
                    self.pass_col_input.setText(config["pass_col"])
                
                if "branch_col" in config and config["branch_col"]:
                    self.branch_col_input.setText(config["branch_col"])
                
                self.data_display.setText("✅ Đã tải cấu hình từ file config.json")
                
                # Tự động kết nối nếu có URL nhưng không hiển thị MessageBox
                if "sheet_url" in config and config["sheet_url"]:
                    # Đặt một timer để kết nối sau khi giao diện đã được khởi tạo
                    QTimer.singleShot(500, self.connect_to_sheet)
                
        except Exception as e:
            self.data_display.setText(f"⚠️ Không thể tải cấu hình: {str(e)}")
    
    def get_column_index(self, column_letter):
        """Chuyển đổi chữ cột (A, B, C...) sang index (0, 1, 2...)"""
        column_letter = column_letter.upper()
        if len(column_letter) == 1 and column_letter in self.column_map:
            return self.column_map[column_letter]
        return -1  # Không hợp lệ
    
    def connect_to_sheet(self):
        creds_path = self.credentials_path
        sheet_url = self.sheet_url_input.text()
        worksheet_name = self.worksheet_input.text()
        
        try:
            header_row = int(self.header_row_input.text())
            if header_row < 1:
                header_row = 1
        except ValueError:
            header_row = 1
        
        if not os.path.exists(creds_path):
            QMessageBox.warning(self, "Lỗi", f"Không tìm thấy file credentials.json tại {creds_path}!")
            return
        
        if not sheet_url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập URL Google Sheet!")
            return
        
        try:
            # Kết nối đến Google Sheets API
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(credentials)
            
            # Mở Google Sheet
            sheet = client.open_by_url(sheet_url)
            
            # Lấy worksheet theo tên
            self.worksheet = sheet.worksheet(worksheet_name)
            
            # Lấy tất cả dữ liệu (bao gồm header row)
            all_values = self.worksheet.get_all_values()
            self.all_data = all_values  # Lưu toàn bộ dữ liệu
            
            if not all_values or len(all_values) <= header_row:
                QMessageBox.warning(self, "Lỗi", "Không đủ dữ liệu trong Sheet hoặc hàng tiêu đề không tồn tại!")
                return
            
            # Lấy header từ hàng được chỉ định
            headers = all_values[header_row - 1]
            
            # Chỉ lấy dữ liệu từ cột C đến cột P (index 2 đến 15)
            start_col = 2  # Cột C (index bắt đầu từ 0)
            end_col = 15   # Cột P
            
            # Đảm bảo không vượt quá số cột có sẵn
            end_col = min(end_col, len(headers) - 1)
            
            if start_col > end_col or start_col >= len(headers):
                QMessageBox.warning(self, "Lỗi", "Không có đủ cột trong Google Sheet để hiển thị từ cột C đến cột P!")
                return
            
            # Lấy headers từ vùng cần thiết
            selected_headers = headers[start_col:end_col + 1]
            
            # Kiểm tra và sửa các headers trùng lặp
            unique_headers = []
            header_count = {}
            
            for header in selected_headers:
                if not header:
                    header = "Column"  # Đặt tên mặc định cho cột trống
                
                if header in header_count:
                    header_count[header] += 1
                    unique_headers.append(f"{header}_{header_count[header]}")
                else:
                    header_count[header] = 0
                    unique_headers.append(header)
            
            # Lấy dữ liệu từ hàng sau header
            data_values = all_values[header_row:]
            
            # Tạo danh sách các bản ghi
            records = []
            for row in data_values:
                # Đảm bảo row có đủ cột cho vùng cần lấy
                if len(row) <= start_col:
                    # Bỏ qua hàng nếu không có đủ dữ liệu
                    continue
                
                # Lấy dữ liệu từ cột C tới cột O
                selected_values = row[start_col:end_col + 1]
                
                # Đảm bảo dữ liệu có đủ số cột
                while len(selected_values) < len(unique_headers):
                    selected_values.append("")
                
                # Cắt bớt nếu có quá nhiều dữ liệu
                if len(selected_values) > len(unique_headers):
                    selected_values = selected_values[:len(unique_headers)]
                
                record = dict(zip(unique_headers, selected_values))
                records.append(record)
            
            if not records:
                QMessageBox.warning(self, "Lỗi", "Không có dữ liệu trong vùng được chọn!")
                return
                
            # Chuyển sang DataFrame để dễ xử lý
            self.df = pd.DataFrame(records)
            self.original_df = self.df.copy()  # Lưu bản sao của DataFrame gốc
            
            # Cập nhật combo box với tên các cột
            self.column_combo.clear()
            self.column_combo.addItems(self.df.columns)
            # Cập nhật combobox lọc nhánh
            
            # Cập nhật bảng dữ liệu
            self.apply_filters()
            
            # Cập nhật thông tin vào data_display thay vì hiển thị MessageBox
            self.data_display.setText(f"✅ Đã kết nối và tải dữ liệu thành công! Số bản ghi: {len(records)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể kết nối đến Google Sheet: {str(e)}")
            # In thêm chi tiết lỗi vào data_display để debug
            self.data_display.setText(f"Chi tiết lỗi:\n{str(e)}\n\nLoẠI: {type(e).__name__}")
    
    def apply_filters(self):
        """Chỉ hiển thị toàn bộ dữ liệu, không lọc theo nhánh hay tìm kiếm sàn nữa"""
        if self.df is None:
            return
        filtered_df = self.df.copy()
        self.display_filtered_data(filtered_df)
    
    def display_filtered_data(self, filtered_df):
        if filtered_df is None:
            return
        self.data_table.setRowCount(len(filtered_df))
        self.data_table.setColumnCount(len(filtered_df.columns) + 1)
        headers = ["Chọn"] + list(filtered_df.columns)
        self.data_table.setHorizontalHeaderLabels(headers)
        for row in range(len(filtered_df)):
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            # Lưu index gốc của dòng vào item để dùng khi đăng nhập
            orig_index = filtered_df.index[row]
            checkbox_item.setData(Qt.UserRole, orig_index)
            self.data_table.setItem(row, 0, checkbox_item)
            for col in range(len(filtered_df.columns)):
                value = str(filtered_df.iloc[row, col])
                if filtered_df.columns[col].lower() in ["password", "pass", "mật khẩu", "mat khau"] or "pass" in filtered_df.columns[col].lower():
                    if value:
                        value = '*' * len(value)
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.data_table.setItem(row, col + 1, item)
        self.data_table.setColumnWidth(0, 50)
        header = self.data_table.horizontalHeader()
        for col in range(1, len(headers)):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
    
    def display_column_data(self):
        if self.df is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng kết nối đến Google Sheet trước!")
            return
        
        selected_column = self.column_combo.currentText()
        
        if not selected_column:
            QMessageBox.warning(self, "Lỗi", "Không có cột nào được chọn!")
            return
        
        # Hiển thị dữ liệu từ cột đã chọn
        data_text = f"Dữ liệu trong cột '{selected_column}':\n\n"
        
        for i, value in enumerate(self.df[selected_column]):
            data_text += f"{i+1}. {value}\n"
        
        self.data_display.setText(data_text)
    
    def login_to_mt(self):
        """Đăng nhập vào MT4/MT5 với tài khoản đã chọn"""
        if self.all_data is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng kết nối đến Google Sheet trước!")
            return
        # Tìm tất cả các hàng được chọn (có checkbox được tích)
        selected_orig_indexes = []
        for row in range(self.data_table.rowCount()):
            checkbox_item = self.data_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                orig_index = checkbox_item.data(Qt.UserRole)
                if orig_index is not None:
                    selected_orig_indexes.append(orig_index)
        if not selected_orig_indexes:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất một tài khoản để đăng nhập!")
            return
        # Lấy các cột đã cấu hình
        try:
            broker_col = self.get_column_index(self.broker_col_input.text())
            server_col = self.get_column_index(self.server_col_input.text())
            login_col = self.get_column_index(self.login_col_input.text())
            pass_col = self.get_column_index(self.pass_col_input.text())
            branch_col = self.get_column_index(self.branch_col_input.text())
            if broker_col < 0 or server_col < 0 or login_col < 0 or pass_col < 0 or branch_col < 0:
                QMessageBox.warning(self, "Lỗi", "Cấu hình cột không hợp lệ! Vui lòng nhập chữ cái cột (A, B, C...)")
                return
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Lỗi khi xử lý cấu hình cột: {str(e)}")
            return
        # Lấy header row từ cấu hình
        try:
            header_row = int(self.header_row_input.text()) - 1
            if header_row < 0:
                header_row = 0
        except ValueError:
            header_row = 0
        # Thông tin các tài khoản sẽ đăng nhập
        accounts_to_login = []
        # Lấy dữ liệu từ các index gốc đã chọn
        for orig_index in selected_orig_indexes:
            try:
                sheet_row_index = header_row + 1 + orig_index
                if sheet_row_index >= len(self.all_data):
                    self.data_display.append(f"⚠️ Không tìm thấy dữ liệu cho hàng gốc {orig_index + 1}!")
                    continue
                row_data = self.all_data[sheet_row_index]
                if len(row_data) <= max(broker_col, server_col, login_col, pass_col, branch_col):
                    self.data_display.append(f"⚠️ Hàng gốc {orig_index + 1} không có đủ cột theo cấu hình!")
                    continue
                broker_name = row_data[broker_col]
                server_name = row_data[server_col]
                login_id = row_data[login_col]
                password = row_data[pass_col]
                branch_name = row_data[branch_col]
                if not login_id or not password:
                    self.data_display.append(f"⚠️ Hàng gốc {orig_index + 1}: Login ID hoặc Password không được để trống!")
                    continue
                accounts_to_login.append({
                    "broker": broker_name,
                    "server": server_name,
                    "login_id": login_id,
                    "password": password,
                    "branch_name": branch_name,
                    "row_index": orig_index
                })
            except Exception as e:
                self.data_display.append(f"❌ Lỗi khi xử lý hàng gốc {orig_index + 1}: {str(e)}")
        if not accounts_to_login:
            QMessageBox.warning(self, "Lỗi", "Không có tài khoản nào hợp lệ để đăng nhập!")
            return
        # Hiển thị danh sách tài khoản sắp đăng nhập
        info = "============ DANH SÁCH TÀI KHOẢN SẮP ĐĂNG NHẬP ============\n"
        for i, acc in enumerate(accounts_to_login):
            info += f"{i+1}. Broker/Sàn: {acc['broker']}\n"
            info += f"   Server: {acc['server']}\n"
            info += f"   Login ID: {acc['login_id']}\n"
            info += f"   Password: {'*' * len(acc['password'])}\n"
            info += f"   Branch: {acc['branch_name']}\n"
            info += "   --------------------------------------\n"
        
        # Xác nhận từ người dùng
        confirm = QMessageBox.question(
            self, 
            "Xác nhận đăng nhập", 
            f"Bạn muốn đăng nhập với {len(accounts_to_login)} tài khoản đã chọn?", 
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Hiển thị thông tin đăng nhập
            self.data_display.setText(info)
            QApplication.processEvents()  # Cập nhật giao diện
            
            # Tiến hành đăng nhập từng tài khoản
            success_count = 0
            failed_count = 0
            
            for acc in accounts_to_login:
                try:
                    # Đăng nhập từng tài khoản
                    self.data_display.append(f"🔄 Đang đăng nhập tài khoản {acc['login_id']}...")
                    QApplication.processEvents()  # Cập nhật giao diện
                    
                    # Sử dụng hàm perform_login hiện có và lấy kết quả
                    result = self.perform_login(acc['login_id'], acc['password'], acc['server'], acc['broker'])
                    
                    # Kiểm tra kết quả đăng nhập
                    if result > 0:
                        success_count += result
                    else:
                        failed_count += 1
                    
                    # Đợi một chút giữa các lần đăng nhập
                    time.sleep(1)  # Đợi 1 giây giữa các lần đăng nhập
                    
                except Exception as e:
                    self.data_display.append(f"❌ Lỗi khi đăng nhập tài khoản {acc['login_id']}: {str(e)}")
                    failed_count += 1
            
            # Hiển thị tóm tắt kết quả
            summary = f"\n✅ Đã gửi thông tin đăng nhập cho {success_count}/{len(accounts_to_login)} tài khoản."
            if failed_count > 0:
                summary += f"\n❌ {failed_count} tài khoản gặp lỗi khi đăng nhập."
            
            self.data_display.append(summary)
            
            # Tự động bỏ chọn tất cả các tài khoản đã chọn
            for row in range(self.data_table.rowCount()):
                checkbox_item = self.data_table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    checkbox_item.setCheckState(Qt.Unchecked)
            
            # Hiển thị MessageBox thông báo kết quả CHỈ KHI ĐÃ HOÀN THÀNH tất cả
            QMessageBox.information(
                self, 
                "Kết quả đăng nhập", 
                f"Đã gửi thông tin đăng nhập cho {success_count}/{len(accounts_to_login)} tài khoản."
            )
    
    def find_field_by_keywords(self, fields, keywords):
        """Tìm trường phù hợp dựa trên từ khóa"""
        for field in fields:
            field_lower = field.lower()
            for keyword in keywords:
                if keyword.lower() in field_lower:
                    return field
        return None
    
    def detect_platform_type(self, window_obj):
        """Xác định loại nền tảng (MT4 hoặc MT5) dựa vào quy trình thực thi
        
        MT4 sử dụng: terminal.exe
        MT5 sử dụng: terminal64.exe
        """
        try:
            # Lấy process ID của cửa sổ
            process_id = None
            try:
                process_id = window_obj.process_id()
            except Exception as e:
                print(f"Không thể lấy process_id: {str(e)}")
                return "MT4"  # Mặc định là MT4 nếu không lấy được process ID
            
            # Chuẩn bị biến để lưu trữ kết quả
            platform_log = f"Process ID: {process_id}\n"
            
            # Sử dụng danh sách process hiện tại để xác định
            try:
                all_processes = {proc.pid: proc.name() for proc in psutil.process_iter(['pid', 'name'])}
                platform_log += f"Found processes: {len(all_processes)}\n"
                print(platform_log)
                
                # Lấy tên process dựa vào process_id
                if process_id in all_processes:
                    process_name = all_processes[process_id].lower()
                    platform_log += f"Process name: {process_name}\n"
                    print(platform_log)
                    
                    # Kiểm tra tên process
                    if "terminal64" in process_name:
                        print(f"Phát hiện MT5 từ tên process: {process_name}")
                        return "MT5"
                    elif "terminal" in process_name and "64" not in process_name:
                        print(f"Phát hiện MT4 từ tên process: {process_name}")
                        return "MT4"
            except Exception as process_err:
                print(f"Lỗi khi xác định qua process: {str(process_err)}")
            
            # Nếu không xác định được qua process, thử thông qua tên cửa sổ
            window_title = window_obj.window_text()
            platform_log += f"Window title: {window_title}\n"
            print(platform_log)
            
            # Kiểm tra tên cửa sổ
            title_lower = window_title.lower()
            if "mt5" in title_lower or "metatrader 5" in title_lower:
                print(f"Phát hiện MT5 từ tiêu đề: {window_title}")
                return "MT5"
            elif "mt4" in title_lower or "metatrader 4" in title_lower:
                print(f"Phát hiện MT4 từ tiêu đề: {window_title}")
                return "MT4"
            
            # Phân tích thêm từ tiêu đề
            if "5." in title_lower and "meta" in title_lower:
                print(f"Phát hiện MT5 từ phiên bản: {window_title}")
                return "MT5"
            elif "4." in title_lower and "meta" in title_lower:
                print(f"Phát hiện MT4 từ phiên bản: {window_title}")
                return "MT4"
                
            # Mặc định là MT4
            print(f"Không xác định được, mặc định là MT4: {window_title}")
            return "MT4"
            
        except Exception as e:
            print(f"Lỗi khi xác định loại nền tảng: {str(e)}")
            return "MT4"  # Mặc định là MT4 nếu xảy ra lỗi
            
    def perform_login(self, login_id, password, server_name, broker_name):
        """Thực hiện đăng nhập vào tất cả các MT4/MT5 có cùng tên sàn"""
        try:
            # Tải cấu hình từ file nếu có
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mt_login_config.json")
            speed_settings = {
                "focus_delay": 0.5,      # Thời gian chờ sau khi focus cửa sổ (giây)
                "key_delay": 0.1,        # Thời gian chờ giữa các phím (giây)
                "form_open_delay": 1.0,  # Thời gian chờ form đăng nhập mở (giây)
                "field_delay": 0.2       # Thời gian chờ giữa các trường (giây)
            }
            
            try:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        if "speed_settings" in config:
                            speed_settings = config["speed_settings"]
            except Exception as config_err:
                print(f"Không thể tải cấu hình tốc độ: {str(config_err)}")
            
            # Khởi tạo COM ở đây để đảm bảo nó được khởi tạo đúng cách trong thread hiện tại
            try:
                pythoncom.CoInitialize()
                print("COM re-initialized before desktop access")
            except Exception as com_err:
                print(f"Warning: COM re-initialization error: {str(com_err)}")
                # Tiếp tục dù có lỗi COM
            
            # Tìm cửa sổ MT4/5
            windows = []
            try:
                # Sử dụng Desktop() với xử lý lỗi tốt hơn
                desktop = Desktop(backend="win32")
                windows = desktop.windows()
                print(f"Found {len(windows)} windows")
            except Exception as e:
                error_msg = f"Lỗi khi lấy danh sách cửa sổ: {str(e)}"
                print(error_msg)
                self.data_display.setText(f"❌ {error_msg}\n\nChi tiết: {type(e).__name__}")
                raise Exception(error_msg)  # Ném lỗi để hàm gọi bắt
            
            # Log thông tin tìm kiếm
            log_text = f"🔍 ĐANG TÌM TẤT CẢ CỬA SỔ MT4/5 CÓ CHỨA TÊN SÀN: {broker_name}\n"
            log_text += "🧭 Danh sách cửa sổ đang mở:\n"
            
            # Đảm bảo broker_name không trống
            if not broker_name or broker_name.strip() == "":
                broker_name = "MetaTrader"
                log_text += "⚠️ Tên sàn trống, sẽ tìm cửa sổ với từ khóa 'MetaTrader'\n"
            
            # Chuẩn hóa broker_name để tăng khả năng tìm kiếm
            broker_keywords = [broker_name.lower()]
            
            # Thêm các biến thể phổ biến của tên sàn
            if "exness" in broker_name.lower():
                broker_keywords.extend(["exness"])
            elif "fbs" in broker_name.lower():
                broker_keywords.extend(["fbs"])
            elif "fxtm" in broker_name.lower():
                broker_keywords.extend(["fxtm", "forextime"])
            elif "forex4you" in broker_name.lower():
                broker_keywords.extend(["forex4you", "f4y"])
            elif "admiral" in broker_name.lower():
                broker_keywords.extend(["admiral", "admirals", "admiralmarkets"])
            elif "skilling" in broker_name.lower():
                broker_keywords.extend(["skilling", "skillinglimited"])
            elif "tickmill" in broker_name.lower():
                broker_keywords.extend(["tickmill"])
            elif "tmgm" in broker_name.lower():
                broker_keywords.extend(["tmgm", "trademax", "trademaxglobal", "trademaximum"])
            elif "valutrade" in broker_name.lower():
                broker_keywords.extend(["valutrade", "valutrading", "valutrades"])
            elif "xm" in broker_name.lower():
                broker_keywords.extend(["xm", "trading point", "tradingpoint"])
            
            # THÊM MỚI: Phân tích server_name để tạo thêm từ khóa tìm kiếm
            server_keywords = []
            if server_name:
                # Chuẩn hóa server_name
                server_name_lower = server_name.lower().strip()
                
                # Thêm toàn bộ server_name vào từ khóa tìm kiếm
                server_keywords.append(server_name_lower)
                
                # Tách server_name thành các phần để phân tích
                server_parts = re.split(r'[-_\s]+', server_name_lower)
                
                # Thêm các phần có độ dài > 3 ký tự vào từ khóa tìm kiếm (loại trừ một số từ chung)
                common_terms = ['live', 'demo', 'real', 'test', 'mt4', 'mt5', 'server']
                for part in server_parts:
                    if len(part) > 3 and part.lower() not in common_terms:
                        server_keywords.append(part)
                
                # Tạo ra dạng không có số version (ví dụ: TradeMaxGlobal-Live10 -> TradeMaxGlobal)
                server_base = re.sub(r'[-_]live\d+$|[-_]demo\d+$|[-_]real\d+$', '', server_name_lower)
                if server_base != server_name_lower:
                    server_keywords.append(server_base)
                
                # Log danh sách từ khóa server để debug
                print(f"Server keywords: {server_keywords}")
            
            # Thêm từ khóa MetaTrader
            mt_keywords = ["metatrader", "mt4", "mt5"]
            
            # Log danh sách từ khóa broker để debug
            print(f"Broker keywords: {broker_keywords}")
            
            # Hiển thị danh sách cửa sổ và tìm kiếm cửa sổ phù hợp
            matching_windows = []
            
            for win in windows:
                try:
                    # Lấy tiêu đề cửa sổ một cách an toàn
                    window_text = ""
                    try:
                        window_text = win.window_text()
                    except Exception as e:
                        print(f"Không thể lấy tiêu đề cửa sổ: {str(e)}")
                        continue
                    
                    if not window_text:
                        continue
                        
                    title = window_text.lower()
                    log_text += f"- {window_text}\n"
                    
                    # Tính điểm ưu tiên cho cửa sổ
                    priority = 0
                    match_reasons = []
                    
                    # THÊM MỚI: Kiểm tra xem login_id có trong tiêu đề không (ưu tiên cao nhất)
                    if str(login_id) in title:
                        priority += 3
                        match_reasons.append(f"Login ID {login_id} khớp")
                    
                    # Kiểm tra xem cửa sổ có chứa tên sàn không
                    broker_match = False
                    for keyword in broker_keywords:
                        if keyword in title:
                            broker_match = True
                            priority += 1
                            match_reasons.append(f"Broker khớp: '{keyword}'")
                            break
                    
                    # THÊM MỚI: Kiểm tra xem cửa sổ có chứa server name không
                    server_match = False
                    for keyword in server_keywords:
                        if keyword in title:
                            server_match = True
                            priority += 1
                            match_reasons.append(f"Server khớp: '{keyword}'")
                            break
                    
                    # Kiểm tra xem cửa sổ có chứa từ khóa MetaTrader không
                    mt_match = False
                    for keyword in mt_keywords:
                        if keyword in title:
                            mt_match = True
                            priority += 0.5  # Ưu tiên thấp hơn
                            match_reasons.append(f"MetaTrader khớp: '{keyword}'")
                            break
                    
                    # Nếu có ít nhất một khớp, thêm vào danh sách cửa sổ phù hợp
                    if broker_match or server_match or (mt_match and priority > 0):
                        # Xác định loại nền tảng (MT4/MT5)
                        try:
                            platform_type = self.detect_platform_type(win)
                        except Exception as platform_err:
                            print(f"Lỗi khi xác định nền tảng: {str(platform_err)}")
                            platform_type = "MT4"  # Mặc định là MT4 nếu có lỗi
                            
                        matching_windows.append({
                            "window": win, 
                            "priority": priority, 
                            "title": window_text,
                            "platform": platform_type,
                            "match_reasons": match_reasons
                        })
                except Exception as window_err:
                    print(f"Lỗi khi xử lý cửa sổ: {str(window_err)}")
                    continue
            
            # Sắp xếp các cửa sổ theo mức độ ưu tiên
            matching_windows.sort(key=lambda x: x["priority"], reverse=True)
            
            # Log thông tin các cửa sổ phù hợp
            if matching_windows:
                log_text += f"\n✅ ĐÃ TÌM THẤY {len(matching_windows)} CỬA SỔ PHÙ HỢP:\n"
                for i, win_info in enumerate(matching_windows):
                    match_reason_text = ", ".join(win_info["match_reasons"])
                    log_text += f"   {i+1}. [{win_info['priority']}] {win_info['title']} ({win_info['platform']}) - Lý do: {match_reason_text}\n"
                    
                # Lọc và giữ lại chỉ các cửa sổ có mức ưu tiên cao nhất
                highest_priority = matching_windows[0]["priority"]
                matching_windows = [w for w in matching_windows if w["priority"] == highest_priority]
                log_text += f"\n🔝 CHỌN {len(matching_windows)} CỬA SỔ CÓ ƯU TIÊN CAO NHẤT ({highest_priority}):\n"
                for i, win_info in enumerate(matching_windows):
                    log_text += f"   {i+1}. {win_info['title']} ({win_info['platform']})\n"
            else:
                log_text += "\n❌ Không tìm thấy cửa sổ MetaTrader nào!"
                self.data_display.append(log_text)
                raise Exception("Không tìm thấy cửa sổ MetaTrader! Vui lòng mở MT4/MT5 trước.")
            
            # Lưu số lượng cửa sổ đã đăng nhập thành công
            successful_logins = 0
            
            # Thực hiện đăng nhập cho từng cửa sổ tìm thấy
            for win_info in matching_windows:
                window_obj = win_info["window"]
                window_title = win_info["title"]
                platform_type = win_info["platform"]
                
                log_text += f"\n\n🔄 ĐANG ĐĂNG NHẬP VÀO: {window_title} ({platform_type})\n"
                
                try:
                    # Kết nối đến ứng dụng và focus vào cửa sổ
                    try:
                        window_obj.set_focus()
                    except Exception as focus_err:
                        log_text += f"⚠️ Không thể focus cửa sổ: {str(focus_err)}\n"
                        # Thử phương pháp khác để focus cửa sổ
                        try:
                            window_obj.set_foreground()
                        except Exception as e:
                            log_text += f"⚠️ Không thể set_foreground(): {str(e)}\n"
                            # Thử phương pháp khác nữa - sử dụng tên cửa sổ để tìm kiếm
                            try:
                                # Sử dụng pyautogui để tìm và nhấp vào cửa sổ
                                pyautogui.getWindowsWithTitle(window_title)[0].activate()
                                log_text += "✓ Đã kích hoạt cửa sổ bằng pyautogui\n"
                            except Exception as e2:
                                log_text += f"⚠️ Không thể kích hoạt cửa sổ: {str(e2)}\n"
                            
                    time.sleep(speed_settings["focus_delay"])  # Giảm thời gian chờ sau khi focus
                    
                    # Mở form login
                    log_text += "🔄 ĐANG MỞ FORM LOGIN...\n"
                    
                    # Nhấn Alt+F để mở menu File
                    pyautogui.keyDown('alt')
                    time.sleep(speed_settings["key_delay"])
                    pyautogui.press('f')
                    time.sleep(speed_settings["key_delay"])
                    pyautogui.keyUp('alt')
                    time.sleep(speed_settings["key_delay"])
                    
                    # Nhấn L để chọn Login
                    pyautogui.press('l')
                    time.sleep(speed_settings["form_open_delay"])  # Đợi form login hiện lên
                    
                    # Điền thông tin login theo quy trình khác nhau cho MT4 và MT5
                    log_text += f"🔄 ĐANG ĐIỀN FORM LOGIN ({platform_type}):\n"
                    log_text += "------------------------\n"
                    
                    # Điền Login ID
                    log_text += "➡️ ĐIỀN LOGIN ID...\n"
                    pyperclip.copy(str(login_id).strip())
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(speed_settings["field_delay"])
                    pyautogui.press('tab')
                    time.sleep(speed_settings["field_delay"])
                    
                    # Điền Password
                    log_text += "➡️ ĐIỀN PASSWORD...\n"
                    pyperclip.copy(str(password).strip())
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(speed_settings["field_delay"])
                    pyautogui.press('tab')
                    time.sleep(speed_settings["field_delay"])
                    
                    # Quy trình khác nhau cho MT4 và MT5
                    if platform_type == "MT5":
                        # MT5: Nhấn thêm Tab một lần nữa trước khi điền Server
                        log_text += "➡️ NHẤN TAB THÊM MỘT LẦN (MT5)...\n"
                        pyautogui.press('tab')
                        time.sleep(speed_settings["field_delay"])
                    
                    # Điền Server name nếu có
                    if server_name and server_name.strip():
                        log_text += "➡️ ĐIỀN SERVER...\n"
                        pyperclip.copy(str(server_name).strip())
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(speed_settings["field_delay"])
                    
                    if platform_type == "MT4":
                        # MT4: Tab 2 lần để focus vào nút OK
                        log_text += "➡️ DI CHUYỂN ĐẾN NÚT OK...\n"
                        pyautogui.press('tab')
                        time.sleep(speed_settings["key_delay"])
                        pyautogui.press('tab')
                        time.sleep(speed_settings["key_delay"])
                    else:
                        # MT5: Chỉ cần Tab 1 lần nữa
                        log_text += "➡️ DI CHUYỂN ĐẾN NÚT OK (MT5)...\n"
                        pyautogui.press('tab')
                        time.sleep(speed_settings["key_delay"])
                    
                    # Nhấn Enter để submit
                    log_text += "➡️ NHẤN ENTER ĐỂ ĐĂNG NHẬP...\n"
                    pyautogui.press('enter')
                    
                    log_text += "✅ ĐÃ HOÀN THÀNH QUY TRÌNH ĐĂNG NHẬP!\n"
                    successful_logins += 1
                    
                    # Đợi một khoảng thời gian để form đăng nhập được xử lý xong
                    # trước khi chuyển sang cửa sổ tiếp theo
                    time.sleep(1)  # Giảm thời gian chờ giữa các lần đăng nhập
                    
                except Exception as e:
                    log_text += f"❌ LỖI KHI ĐĂNG NHẬP VÀO CỬA SỔ: {str(e)}\n"
            
            self.data_display.append(log_text)
            
            return successful_logins  # Trả về số lượng đăng nhập thành công thay vì hiển thị thông báo
            
        except Exception as e:
            error_detail = f"LỖI KHI ĐĂNG NHẬP: {str(e)}\nLoại lỗi: {type(e).__name__}"
            self.data_display.append(error_detail)
            print(error_detail)
            import traceback
            traceback.print_exc()
            # Trả về 0 (không có đăng nhập thành công) thay vì hiển thị popup
            return 0
        finally:
            # Giải phóng COM
            try:
                pythoncom.CoUninitialize()
                print("COM uninitialized after login")
            except:
                pass
    
    def find_mt_windows_alternative(self):
        """Phương thức thay thế để tìm cửa sổ MT4/MT5 sử dụng win32gui trực tiếp"""
        found_windows = []
        
        print("===== PHƯƠNG PHÁP THAY THẾ =====")
        
        try:
            # Thử tìm quy trình MT4/MT5 bằng phương pháp khác
            try:
                import win32process
                import win32gui
                import win32con
                
                def enum_windows_callback(hwnd, results):
                    # Chỉ xử lý các cửa sổ hiển thị
                    if win32gui.IsWindowVisible(hwnd):
                        try:
                            # Lấy tiêu đề cửa sổ
                            window_title = win32gui.GetWindowText(hwnd)
                            if not window_title:
                                return True  # Tiếp tục đến cửa sổ tiếp theo
                                
                            # Bỏ qua cửa sổ của ứng dụng này
                            if "MT4/MT5 Login - Google Sheets" in window_title:
                                return True
                                
                            # Tiêu đề quá ngắn thường không phải MT4/MT5
                            if len(window_title) < 15:
                                return True
                                
                            # Kiểm tra xem có phải là cửa sổ MT4/MT5 không
                            title_lower = window_title.lower()
                            
                            # Kiểm tra từ khóa loại trừ trước tiên (để nhanh chóng loại bỏ các cửa sổ không liên quan)
                            exclude_keywords = [
                                "notepad", "chrome", "edge", "firefox", "explorer", "microsoft", 
                                "word", "excel", "powerpoint", "outlook", "access", "onenote",
                                "calculator", "paint", "desktop", "document", "settings", "control panel",
                                "visual studio", "vscode", "code", "cmd", "command", "powershell", "terminal",
                                "settings", "task manager", "file explorer", "file browser", "sql", "database",
                                "antivirus", "defender", "security", "mail", "messaging", "chat", "teams",
                                "discord", "skype", "zoom", "video", "browser", "internet", "spotify",
                                "player", "game", "nvidia", "amd", "intel", "update", "installer", "setup",
                                "system", "config", "properties", "preferences", "options", "help", "about",
                                "cursor", "python", "calculator", "camera", "photos", "gallery", "media",
                                "store", "app", "windows", "adobe", "reader", "acrobat", "photoshop", "illustrator"
                            ]
                            
                            # Kiểm tra từ khóa loại trừ
                            if any(keyword in title_lower for keyword in exclude_keywords):
                                return True
                            
                            # Kiểm tra các pattern cụ thể cho MT4/MT5 
                            # Pattern chính xác cho MT4: 12345678 : ServerName
                            # Pattern chính xác cho MT5: 12345678 - ServerName
                            is_mt4_format = bool(re.search(r'\d{5,10}\s*:\s*[\w\.-]+', window_title))
                            is_mt5_format = bool(re.search(r'\d{5,10}\s*-\s*[\w\.-]+', window_title))
                            
                            # Từ khóa chính xác hơn để nhận diện MT4/MT5
                            mt_keywords = [
                                "metatrader 4", "metatrader 5", 
                                "meta trader 4", "meta trader 5",
                                "metatrader4", "metatrader5"
                            ]
                            
                            # Kiểm tra từ khóa MT chính xác
                            has_mt_keyword = any(keyword in title_lower for keyword in mt_keywords)
                            
                            # 1. Cửa sổ có định dạng MT4 hoặc MT5 rõ ràng sẽ được chấp nhận
                            if is_mt4_format or is_mt5_format:
                                print(f"Win32GUI: Tìm thấy cửa sổ MT với định dạng chuẩn: {window_title}")
                                is_mt_window = True
                            # 2. Nếu không có định dạng rõ ràng nhưng có từ khóa MT4/MT5 chính xác
                            elif has_mt_keyword:
                                print(f"Win32GUI: Tìm thấy cửa sổ MT với từ khóa: {window_title}")
                                is_mt_window = True
                            # 3. Kiểm tra các từ khóa MT chung hơn nếu không tìm thấy theo cách trên
                            else:
                                general_mt_keywords = ["mt4", "mt5", "mt4-", "mt5-", "-mt4", "-mt5"]
                                is_general_mt = any(f" {keyword} " in f" {title_lower} " for keyword in general_mt_keywords)
                                
                                # Kiểm tra xem tiêu đề có chứa cả ID đăng nhập và server không
                                has_login_id = bool(re.search(r'\d{5,10}', window_title))
                                has_server_info = any(server_keyword in title_lower for server_keyword in ["server", "live", "demo", "real"])
                                
                                # Chấp nhận là cửa sổ MT nếu có từ khóa MT và có thông tin ID hoặc server
                                is_mt_window = is_general_mt and (has_login_id or has_server_info)
                                
                                if is_mt_window:
                                    print(f"Win32GUI: Tìm thấy cửa sổ MT với từ khóa chung: {window_title}")
                            
                            if is_mt_window:
                                # Phân tích tiêu đề để lấy thông tin tài khoản
                                account_info = self.extract_account_info_from_title(window_title)
                                
                                # Chỉ thêm vào kết quả nếu có login_id hoặc server
                                if account_info.get("login_id") or account_info.get("server"):
                                    # Xác định loại nền tảng
                                    platform_type = ""
                                    if is_mt4_format or "mt4" in title_lower:
                                        platform_type = "MT4"
                                    elif is_mt5_format or "mt5" in title_lower:
                                        platform_type = "MT5"
                                    else:
                                        platform_type = "MT4"  # Mặc định
                                        
                                    # Thêm vào danh sách kết quả
                                    window_info = {
                                        "title": window_title,
                                        "hwnd": hwnd,
                                        "platform": platform_type,
                                        "login_id": account_info.get("login_id", ""),
                                        "broker": account_info.get("broker", ""),
                                        "server": account_info.get("server", "")
                                    }
                                    results.append(window_info)
                        except Exception as e:
                            print(f"Lỗi khi xử lý cửa sổ: {str(e)}")
                    
                    return True  # Tiếp tục liệt kê
                
                # Thực hiện liệt kê tất cả các cửa sổ
                windows = []
                win32gui.EnumWindows(enum_windows_callback, windows)
                
                print(f"Win32GUI: Tìm thấy {len(windows)} cửa sổ MT4/MT5")
                
                # Chuyển đổi sang định dạng kết quả
                for win in windows:
                    terminal_info = {
                        "title": win["title"],
                        "platform": win["platform"],
                        "login_id": win["login_id"],
                        "broker": win["broker"],
                        "server": win["server"]
                    }
                    found_windows.append(terminal_info)
                
            except ImportError as e:
                print(f"Win32GUI: Không thể import thư viện cần thiết: {str(e)}")
            except Exception as e:
                print(f"Win32GUI: Lỗi khi tìm cửa sổ: {str(e)}")
                
        except Exception as e:
            print(f"Lỗi tổng quát trong phương pháp thay thế: {str(e)}")
            
        return found_windows
        
    def find_running_terminals(self):
        """Tìm tất cả các cửa sổ MT4/MT5 đang chạy và lấy thông tin tài khoản"""
        running_terminals = []
        
        try:
            print("====== BẮT ĐẦU QUÉT ======")
            
            # In ra thông tin debug về hệ thống
            system_info = f"OS: {sys.platform}, Python: {sys.version}"
            print(f"Thông tin hệ thống: {system_info}")
            
            # Lấy danh sách các process đang chạy với tên là terminal.exe hoặc terminal64.exe
            mt4_processes = []
            mt5_processes = []
            
            # Danh sách tên tiến trình MT4/MT5 có thể có
            mt4_process_names = ["terminal.exe", "metatrader4.exe", "mt4.exe"]
            mt5_process_names = ["terminal64.exe", "metatrader5.exe", "mt5.exe"]
            
            # In thông tin debug về quy trình
            print("Đang quét các quy trình MT4/MT5...")
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower() if 'name' in proc_info else ""
                    if proc_name:
                        if any(mt4_name in proc_name for mt4_name in mt4_process_names):
                            mt4_processes.append(proc_info['pid'])
                            print(f"Found MT4 process: {proc_name} (PID: {proc_info['pid']})")
                        elif any(mt5_name in proc_name for mt5_name in mt5_process_names):
                            mt5_processes.append(proc_info['pid'])
                            print(f"Found MT5 process: {proc_name} (PID: {proc_info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            print(f"Found MT4 processes: {len(mt4_processes)}, PIDs: {mt4_processes}")
            print(f"Found MT5 processes: {len(mt5_processes)}, PIDs: {mt5_processes}")
            
            # Sử dụng thông tin PID để lọc cửa sổ
            mt_process_ids = mt4_processes + mt5_processes
            
            # Thử phương pháp Win32GUI để tìm cửa sổ của các process MT4/MT5
            if mt_process_ids:
                try:
                    # Tìm cửa sổ thuộc các process MT4/MT5 đã phát hiện
                    windows_from_processes = []
                    
                    def enum_process_windows(hwnd, results):
                        if win32gui.IsWindowVisible(hwnd):
                            try:
                                # Lấy ID process của cửa sổ
                                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                                
                                # Kiểm tra xem cửa sổ có thuộc MT4/MT5 process không
                                if pid in mt_process_ids:
                                    window_title = win32gui.GetWindowText(hwnd)
                                    
                                    # Bỏ qua cửa sổ con không có tiêu đề hoặc tiêu đề quá ngắn
                                    if not window_title or len(window_title) < 10:
                                        return True
                                    
                                    # Kiểm tra xem có phải cửa sổ chính không
                                    platform_type = "MT4" if pid in mt4_processes else "MT5"
                                    
                                    # Phân tích thông tin tài khoản từ tiêu đề cửa sổ
                                    account_info = self.extract_account_info_from_title(window_title)
                                    
                                    # Chỉ thêm vào danh sách kết quả nếu có ít nhất một trong login_id hoặc server
                                    if account_info.get("login_id") or account_info.get("server"):
                                        results.append({
                                            "title": window_title,
                                            "process_id": pid,
                                            "hwnd": hwnd,
                                            "platform": platform_type,
                                            "login_id": account_info.get("login_id", ""),
                                            "broker": account_info.get("broker", ""),
                                            "server": account_info.get("server", "")
                                        })
                                        print(f"Found MT window from process: {window_title}")
                            except Exception as e:
                                print(f"Error handling window in process: {str(e)}")
                            
                        return True
                    
                    win32gui.EnumWindows(enum_process_windows, windows_from_processes)
                    
                    if windows_from_processes:
                        print(f"Found {len(windows_from_processes)} windows from MT processes")
                        for win in windows_from_processes:
                            terminal_info = {
                                "title": win["title"],
                                "platform": win["platform"],
                                "login_id": win["login_id"],
                                "broker": win["broker"],
                                "server": win["server"]
                            }
                            running_terminals.append(terminal_info)
                        
                        # Nếu đã tìm thấy cửa sổ từ các process MT, trả về luôn
                        if running_terminals:
                            return running_terminals
                except Exception as e:
                    print(f"Error when finding windows from processes: {str(e)}")
            
            # Nếu không tìm thấy quy trình MT4/MT5 hoặc không tìm thấy cửa sổ, thử lấy tất cả các cửa sổ
            print("Đang quét tất cả các cửa sổ...")
            
            try:
                # Mã trước đây sử dụng pywinauto Desktop
                desktop = Desktop(backend="win32")
                windows = desktop.windows()
                print(f"Tìm thấy {len(windows)} cửa sổ bằng pywinauto")
                
                # Từ khóa chính xác hơn để nhận diện MT4/MT5
                mt_keywords = [
                    "metatrader 4", "metatrader 5", 
                    "meta trader 4", "meta trader 5",
                    "metatrader4", "metatrader5"
                ]
                
                # Từ khóa loại trừ (cửa sổ không phải MT4/MT5)
                exclude_keywords = [
                    "notepad", "chrome", "edge", "firefox", "explorer", 
                    "word", "excel", "powerpoint", "outlook", 
                    "calculator", "paint", "desktop", "document",
                    "visual studio", "vscode", "cmd", "powershell", 
                    "settings", "task manager", "file explorer"
                ]
                
                # Lọc cửa sổ
                for win in windows:
                    try:
                        title = win.window_text()
                        
                        # Bỏ qua cửa sổ không có tiêu đề hoặc tiêu đề quá ngắn
                        if not title or len(title) < 15:
                            continue
                            
                        # Kiểm tra nếu trong từ khóa loại trừ
                        title_lower = title.lower()
                        if any(keyword in title_lower for keyword in exclude_keywords):
                            continue
                            
                        # Kiểm tra định dạng chuẩn của MT4/MT5
                        is_mt4_format = bool(re.search(r'\d{5,10}\s*:\s*[\w\.-]+', title))
                        is_mt5_format = bool(re.search(r'\d{5,10}\s*-\s*[\w\.-]+', title))
                        
                        # Kiểm tra từ khóa MT chính xác
                        has_mt_keyword = any(keyword in title_lower for keyword in mt_keywords)
                        
                        # Nếu không có định dạng chuẩn hoặc từ khóa chính xác, bỏ qua
                        if not (is_mt4_format or is_mt5_format or has_mt_keyword):
                            continue
                            
                        # Phân tích thông tin tài khoản từ tiêu đề
                        account_info = self.extract_account_info_from_title(title)
                        
                        # Chỉ thêm vào danh sách kết quả nếu có ít nhất một trong login_id hoặc server
                        if account_info.get("login_id") or account_info.get("server"):
                            # Xác định loại nền tảng (MT4 hoặc MT5)
                            platform_type = ""
                            if is_mt4_format or "mt4" in title_lower:
                                platform_type = "MT4"
                            elif is_mt5_format or "mt5" in title_lower:
                                platform_type = "MT5"
                            else:
                                platform_type = "MT4"  # Mặc định
                                
                            # Thêm vào danh sách kết quả
                            terminal_info = {
                                "title": title,
                                "platform": platform_type,
                                "login_id": account_info.get("login_id", ""),
                                "broker": account_info.get("broker", ""),
                                "server": account_info.get("server", "")
                            }
                            running_terminals.append(terminal_info)
                            print(f"Pywinauto: Cửa sổ MT: {title}")
                    except Exception as e:
                        print(f"Lỗi khi xử lý cửa sổ: {str(e)}")
                        
            except Exception as e:
                print(f"Lỗi khi sử dụng pywinauto Desktop: {str(e)}")
                # Nếu pywinauto thất bại, thử phương pháp thay thế
                try:
                    backup_terminals = self.find_mt_windows_alternative()
                    return backup_terminals
                except Exception as e2:
                    print(f"Lỗi khi sử dụng phương pháp thay thế: {str(e2)}")
                    return []
                
        except Exception as e:
            print(f"Lỗi tổng quát khi tìm terminals: {str(e)}")
            
        if not running_terminals:
            # Thử phương pháp thay thế nếu không tìm thấy cửa sổ nào
            try:
                running_terminals = self.find_mt_windows_alternative()
            except Exception as e:
                print(f"Lỗi khi sử dụng phương pháp thay thế: {str(e)}")
                
        return running_terminals

    def scan_all_accounts(self):
        """Quét tất cả các tài khoản MT4/MT5 đang chạy và tìm xem chúng thuộc nhánh nào"""
        if self.df is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng kết nối đến Google Sheet trước!")
            return
        
        # Hiển thị thông báo đang quét
        self.data_display.setText(f"🔍 Đang quét tất cả tài khoản MT4/MT5...")
        QApplication.processEvents()
        
        try:
            # Khởi tạo COM
            try:
                pythoncom.CoInitialize()
                print("COM initialized for scanning")
            except Exception as com_err:
                print(f"Warning: COM initialization error: {str(com_err)}")
            
            # Tìm tất cả cửa sổ MT4/MT5 đang chạy
            running_terminals = self.find_running_terminals()
            
            # Nếu không tìm thấy cửa sổ nào, thử phương pháp thay thế
            if not running_terminals:
                print("Không tìm thấy cửa sổ với phương pháp thông thường, thử phương pháp thay thế...")
                running_terminals = self.find_mt_windows_alternative()
            
            if not running_terminals:
                self.data_display.setText("❌ Không tìm thấy cửa sổ MT4/MT5 nào đang chạy!")
                return
                
            # Định vị các cột cần thiết
            login_col_letter = self.login_col_input.text()
            login_col_index = self.get_column_index(login_col_letter)
            
            if login_col_index < 0:
                self.data_display.setText(f"❌ Cột Login ID không hợp lệ: {login_col_letter}")
                return
                
            broker_col_letter = self.broker_col_input.text()
            broker_col_index = self.get_column_index(broker_col_letter)
            
            if broker_col_index < 0:
                self.data_display.setText(f"❌ Cột Broker không hợp lệ: {broker_col_letter}")
                return
            
            # Cột Note1 (thường là cột C có index 2)
            note1_index = self.get_column_index(self.branch_col_input.text())
            if note1_index < 0:
                # Xử lý lỗi hoặc return
                return
            
            # Lấy header row từ cấu hình
            try:
                header_row = int(self.header_row_input.text()) - 1
                if header_row < 0:
                    header_row = 0
            except ValueError:
                header_row = 0
            
            print(f"Bắt đầu quét tất cả tài khoản...")
            
            # In ra header để kiểm tra
            if len(self.all_data) > header_row:
                headers = self.all_data[header_row]
                print(f"Headers: {headers}")
                
                # In ra 10 hàng đầu tiên và toàn bộ dữ liệu của chúng để kiểm tra
                print("\n==== DỮ LIỆU MẪU TOÀN BỘ HÀNG ĐẦU TIÊN ====")
                for i, row in enumerate(self.all_data[header_row+1:header_row+11]):
                    print(f"Hàng {i+1}: {row}")
                print("\n==== KẾT THÚC DỮ LIỆU MẪU ====\n")
            
            # Tạo một từ điển ánh xạ login_id -> thông tin từ bảng dữ liệu
            accounts_map = {}
            
            # Danh sách các từ khóa nhánh phổ biến để tìm kiếm
            branch_keywords = ["nhánh", "branch", "chi nhánh"]
            
            # Danh sách các nhánh cụ thể để tìm kiếm
            specific_branches = [
                "nhánh a khang", "nhánh phát", "nhánh hoàng", "nhánh anh khang",
                "nhánh phú", "nhánh đạt", "nhánh đức", "nhánh tuấn", "nhánh tân",
                "nhánh hải", "nhánh hùng", "nhánh long", "nhánh quân", "nhánh minh",
                "nhánh thái", "nhánh thành", "nhánh son", "nhánh khánh", "nhánh khoa"
            ]
            
            # Mục đích của hàm này là lấy tất cả tài khoản từ bảng dữ liệu
            # và ánh xạ Login ID -> thông tin nhánh, broker, v.v.
            for i, row_data in enumerate(self.all_data[header_row + 1:]):
                # Bỏ qua nếu không đủ cột
                if len(row_data) <= max(login_col_index, broker_col_index, note1_index):
                    continue
                
                # Lấy login ID từ cột đã cấu hình
                login_id = str(row_data[login_col_index]).strip()
                
                # Bỏ qua nếu login ID trống
                if not login_id:
                    continue
                
                # Lấy thông tin nhánh từ cột E (Note1)
                note_value = str(row_data[note1_index]).strip() if note1_index < len(row_data) else ""
                print(f"Login ID: {login_id}, Note1: {note_value}")
                
                # Tìm tên nhánh từ note_value
                branch_name = ""
                
                # Tìm nhánh cụ thể trong note_value
                note_value_lower = note_value.lower()
                
                # Kiểm tra xem note_value có chứa một trong các nhánh cụ thể không
                for specific_branch in specific_branches:
                    if specific_branch in note_value_lower:
                        branch_name = specific_branch
                        print(f"  -> Tìm thấy nhánh cụ thể: {branch_name}")
                        break
                
                # Nếu không tìm thấy trong danh sách cụ thể, thử tìm theo từ khóa
                if not branch_name:
                    for keyword in branch_keywords:
                        if keyword in note_value_lower:
                            parts = note_value_lower.split(keyword)
                            if len(parts) > 1:
                                # Lấy phần sau từ khóa và làm sạch
                                branch_name = keyword + parts[1].strip()
                                print(f"  -> Tìm thấy nhánh từ từ khóa '{keyword}': {branch_name}")
                                break
                
                # Nếu vẫn không tìm thấy từ khóa nhánh, sử dụng toàn bộ giá trị note
                if not branch_name and note_value:
                    branch_name = note_value
                    print(f"  -> Không tìm thấy từ khóa nhánh, sử dụng toàn bộ note: {branch_name}")
                
                # Lấy thông tin sàn
                broker_name = str(row_data[broker_col_index]).strip() if broker_col_index < len(row_data) else ""
                
                # Lưu thông tin vào từ điển
                accounts_map[login_id] = {
                    "broker": broker_name,
                    "branch_name": branch_name,
                    "note": note_value,
                    "row_data": row_data
                }
            
            print(f"Tìm thấy {len(accounts_map)} tài khoản trong bảng dữ liệu")
            # In ra một vài mẫu để kiểm tra
            sample_count = min(5, len(accounts_map))
            if sample_count > 0:
                print(f"Mẫu {sample_count} tài khoản đầu tiên:")
                for i, (login_id, info) in enumerate(list(accounts_map.items())[:sample_count]):
                    print(f"  {i+1}. Login ID: {login_id}, Nhánh: {info['branch_name']}, Note: {info['note']}")
            
            # Kiểm tra các tài khoản đang chạy và tìm xem chúng thuộc nhánh nào
            scan_results = []
            
            for terminal in running_terminals:
                login_id = terminal.get("login_id", "").strip()
                if not login_id:
                    continue  # Bỏ qua nếu không có login ID
                
                broker = terminal.get("broker", "")
                server = terminal.get("server", "")
                platform = terminal.get("platform", "")
                
                # Mặc định không tìm thấy trong bảng dữ liệu
                found_branch = "Không tìm thấy"
                account_note = ""
                
                # Kiểm tra xem tài khoản này có trong bảng dữ liệu không
                if login_id in accounts_map:
                    account_info = accounts_map[login_id]
                    found_branch = account_info["branch_name"] if account_info["branch_name"] else "Không rõ nhánh"
                    account_note = account_info["note"]
                    print(f"Tài khoản {login_id}: Tìm thấy thuộc nhánh '{found_branch}'")
                else:
                    print(f"Tài khoản {login_id}: Không tìm thấy trong bảng dữ liệu")
                
                # Thêm vào kết quả
                scan_results.append({
                    "login_id": login_id,
                    "broker": broker,
                    "server": server,
                    "platform": platform,
                    "title": terminal.get("title", ""),
                    "is_correct_branch": True if login_id in accounts_map else False,
                    "belongs_to_branch": found_branch,
                    "note": account_note
                })
            
            # Hiển thị kết quả quét
            self.display_scan_results(scan_results)
                
        except Exception as e:
            error_detail = f"Lỗi khi quét tài khoản: {str(e)}\nLoại: {type(e).__name__}"
            self.data_display.setText(error_detail)
            print(error_detail)
            import traceback
            traceback.print_exc()  # In chi tiết lỗi để debug
        finally:
            # Giải phóng COM
            try:
                pythoncom.CoUninitialize()
                print("COM uninitialized after scanning")
            except:
                pass

    def display_scan_results(self, scan_results):
        """Hiển thị kết quả quét tài khoản"""
        if not scan_results:
            self.data_display.setText(f"✅ Không tìm thấy tài khoản MT4/MT5 nào đang chạy.")
            self.scan_result_table.setVisible(False)
            return
        # Cấu hình bảng kết quả
        self.scan_result_table.clear()
        self.scan_result_table.setRowCount(len(scan_results))
        self.scan_result_table.setColumnCount(6)
        self.scan_result_table.setHorizontalHeaderLabels(["Login ID", "Server", "Nền tảng", "Trạng thái", "Thuộc nhánh", "Equity"])
        self.scan_result_table.setVisible(True)
        # Thiết lập chiều rộng cột
        column_widths = [100, 120, 80, 120, 150, 120]
        for col, width in enumerate(column_widths):
            self.scan_result_table.setColumnWidth(col, width)
        found_count = 0
        not_found_count = 0
        for row, result in enumerate(scan_results):
            login_id_item = QTableWidgetItem(result["login_id"])
            font = QFont()
            font.setBold(True)
            login_id_item.setFont(font)
            self.scan_result_table.setItem(row, 0, login_id_item)
            # Bỏ cột Sàn, chỉ còn Server
            self.scan_result_table.setItem(row, 1, QTableWidgetItem(result["server"]))
            platform_item = QTableWidgetItem(result["platform"])
            if result["platform"] == "MT4":
                platform_item.setBackground(QColor(173, 216, 230))
            else:
                platform_item.setBackground(QColor(255, 182, 193))
            self.scan_result_table.setItem(row, 2, platform_item)
            status_item = QTableWidgetItem()
            branch_name = result.get("belongs_to_branch", "Không xác định")
            branch_item = QTableWidgetItem(branch_name)
            if result["is_correct_branch"]:
                status_item.setText("✓ Đã tìm thấy")
                status_item.setBackground(QColor(144, 238, 144))
                branch_item.setBackground(QColor(240, 240, 240))
                branch_item.setForeground(QColor(0, 0, 255))
                branch_item.setFont(QFont("Arial", 9, QFont.Bold))
                found_count += 1
            else:
                status_item.setText("⚠️ Không tìm thấy")
                status_item.setBackground(QColor(255, 255, 153))
                not_found_count += 1
            self.scan_result_table.setItem(row, 3, status_item)
            self.scan_result_table.setItem(row, 4, branch_item)
            # Cột Equity
            equity_value = ""
            login_id = result["login_id"]
            equity_col_index = 15  # Cột P - EndEquity (index 15)
            if self.all_data:
                try:
                    header_row = int(self.header_row_input.text()) - 1
                    if header_row < 0:
                        header_row = 0
                except Exception:
                    header_row = 0
                login_col_index = self.get_column_index(self.login_col_input.text())
                for row_data in self.all_data[header_row + 1:]:
                    if len(row_data) > max(login_col_index, equity_col_index):
                        if str(row_data[login_col_index]).strip() == login_id:
                            equity_value = str(row_data[equity_col_index]).strip()
                            break
            equity_item = QTableWidgetItem(equity_value)
            # Nếu equity = 0 thì tô màu đỏ nhạt
            try:
                if equity_value and float(equity_value.replace(",", "").replace(" ", "")) == 0:
                    equity_item.setBackground(QColor(255, 200, 200))
            except:
                pass
            self.scan_result_table.setItem(row, 5, equity_item)
        # Tóm tắt kết quả
        summary = f"""
        === KẾT QUẢ QUÉT TÀI KHOẢN ===
        Số tài khoản đang chạy: {len(scan_results)}
        Đã tìm thấy trong bảng dữ liệu: {found_count}
        Không tìm thấy trong bảng dữ liệu: {not_found_count}
        
        Lưu ý: 
        - Các tài khoản được đánh dấu màu xanh lá ✓ là đã tìm thấy trong bảng dữ liệu.
        - Các tài khoản đánh dấu màu vàng ⚠️ là không tìm thấy trong bảng dữ liệu.
        - Nền tảng MT4 được hiển thị màu xanh dương, MT5 được hiển thị màu hồng.
        """
        
        self.data_display.setText(summary)
        
        # Thông báo kết quả
        if not_found_count > 0 and found_count > 0:
            QMessageBox.information(
                self,
                "Kết quả quét",
                f"Tìm thấy {found_count} tài khoản trong bảng dữ liệu.\nKhông tìm thấy {not_found_count} tài khoản trong bảng dữ liệu!"
            )
        elif not_found_count > 0 and found_count == 0:
            QMessageBox.warning(
                self,
                "Kết quả quét",
                f"Không tìm thấy {not_found_count} tài khoản trong bảng dữ liệu!"
            )
        else:
            QMessageBox.information(
                self,
                "Kết quả quét",
                f"Tìm thấy tất cả {found_count} tài khoản trong bảng dữ liệu!"
            )

    def extract_account_info_from_title(self, title):
        """Trích xuất thông tin tài khoản từ tiêu đề cửa sổ MT4/MT5"""
        account_info = {
            "login_id": "",
            "broker": "",
            "server": ""
        }
        
        try:
            print(f"Đang phân tích tiêu đề: {title}")
            
            # Phân tích tiêu đề theo định dạng chuẩn của MT4/MT5
            # MT4 thường có định dạng: "ID: Tên sàn" hoặc "Tên sàn - ID"
            # MT5 thường có định dạng: "ID - Tên sàn"
            
            # Mẫu chính xác cho MetaTrader
            mt_patterns = [
                # MT4 standard: 12345678 : Demo-Server
                r'(\d{5,10})\s*:\s*([\w\.-]+)',
                # MT5 standard: 12345678 - Demo-Server
                r'(\d{5,10})\s*-\s*([\w\.-]+)',
                # MT pattern with @ symbol: 12345678@Demo-Server
                r'(\d{5,10})@([\w\.-]+)',
                # MT pattern with space: 12345678 Demo-Server
                r'(\d{5,10})\s+([\w\.-]+\b(?:\s+[\w\.-]+){0,2})\b',
                # Broker name followed by ID: BrokerName - 12345678
                r'([\w\.-]+)\s*-\s*(\d{5,10})'
            ]
            
            # Kiểm tra các mẫu chính xác của MT
            matched = False
            for pattern in mt_patterns:
                matches = re.search(pattern, title)
                if matches:
                    # Kiểm tra xem nhóm nào chứa login ID (dãy số)
                    if matches.group(1).isdigit() and 5 <= len(matches.group(1)) <= 10:
                        account_info["login_id"] = matches.group(1)
                        account_info["server"] = matches.group(2)
                    elif matches.group(2).isdigit() and 5 <= len(matches.group(2)) <= 10:
                        account_info["server"] = matches.group(1)
                        account_info["login_id"] = matches.group(2)
                    else:
                        continue
                        
                    print(f"  -> Đã tìm thấy Login ID: {account_info['login_id']} và Server: {account_info['server']}")
                    matched = True
                    break
            
            # Nếu không tìm thấy theo mẫu chuẩn, thử các phương pháp khác
            if not matched:
                # 1. Trích xuất login ID
                login_patterns = [
                    r'login\s*[:#-]?\s*(\d{5,10})',  # Login: 12345678
                    r'account\s*[:#-]?\s*(\d{5,10})',  # Account: 12345678
                    r'id\s*[:#-]?\s*(\d{5,10})',  # ID: 12345678
                    r'no[.:]?\s*(\d{5,10})',  # No: 12345678
                    r'acc[.:]?\s*(\d{5,10})',  # Acc: 12345678
                    r'a/c[.:]?\s*(\d{5,10})',  # A/C: 12345678
                    r'(\d{5,10})@',  # Dãy số theo sau là @ (phổ biến trong MT4/5)
                    r':\s*(\d{5,10})',  # : 12345678
                    r'-\s*(\d{5,10})',  # - 12345678
                ]
                
                for pattern in login_patterns:
                    matches = re.search(pattern, title)
                    if matches:
                        account_info["login_id"] = matches.group(1)
                        print(f"  -> Tìm thấy login ID: {account_info['login_id']} với pattern: {pattern}")
                        break
            
                # Nếu vẫn không tìm thấy login ID, tìm bất kỳ dãy số nào có độ dài phù hợp
                if not account_info["login_id"]:
                    numbers = re.findall(r'\d+', title)
                    for num in numbers:
                        if 5 <= len(num) <= 10:
                            account_info["login_id"] = num
                            print(f"  -> Tìm thấy login ID (backup): {account_info['login_id']}")
                            break
            
                # Xử lý thông tin server nếu chưa có
                if not account_info["server"]:
                    # Thử trích xuất server từ phần sau dấu : hoặc - nếu có login_id
                    if account_info["login_id"]:
                        server_patterns = [
                            rf'{account_info["login_id"]}\s*:\s*([\w\.-]+)',  # ID: server
                            rf'{account_info["login_id"]}\s*-\s*([\w\.-]+)',  # ID - server
                            r'server\s*[:#-]?\s*([\w\.-]+)',  # Server: abc-server
                            r'@([\w\.-]+)',  # ID@server
                        ]
                        
                        for pattern in server_patterns:
                            matches = re.search(pattern, title)
                            if matches:
                                server = matches.group(1)
                                account_info["server"] = server
                                print(f"  -> Tìm thấy server: {account_info['server']} với pattern: {pattern}")
                                break
                    
                    # Nếu vẫn không tìm thấy server, thử tìm các từ khóa liên quan
                    if not account_info["server"]:
                        server_keywords = ["server", "live", "demo", "real", "practice"]
                        
                        for keyword in server_keywords:
                            pattern = rf'{keyword}\s*[:#-]?\s*([\w\.-]+)'
                            matches = re.search(pattern, title.lower()) 
                            if matches:
                                server = matches.group(1)
                                account_info["server"] = server
                                print(f"  -> Tìm thấy server từ từ khóa: {account_info['server']}")
                                break
            
            # 3. Trích xuất tên broker (thường là phần đầu của tiêu đề hoặc được bao gồm trong server)
            # Các sàn phổ biến
            common_brokers = [
                "exness", "fbs", "fxtm", "forex4you", "admiral", 
                "skilling", "tickmill", "instaforex", "hotforex", "fxpro",
                "xtb", "oanda", "fxcm", "ig", "pepperstone", "axiory", "icmarkets",
                "tradingpro", "tradersway", "dukascopy"
            ]
            
            # Nếu server đã có thông tin, thử xác định broker từ server
            if account_info["server"]:
                server_lower = account_info["server"].lower()
                for broker in common_brokers:
                    if broker in server_lower:
                        account_info["broker"] = broker
                        print(f"  -> Tìm thấy broker từ server: {account_info['broker']}")
                        break
            
            # Nếu chưa xác định được broker, thử từ tiêu đề
            if not account_info["broker"]:
                title_lower = title.lower()
                for broker in common_brokers:
                    if f" {broker} " in f" {title_lower} " or f"-{broker}" in title_lower or f"{broker}-" in title_lower:
                        account_info["broker"] = broker
                        print(f"  -> Tìm thấy broker từ tiêu đề: {account_info['broker']}")
                        break
            
            # Nếu không tìm thấy tên sàn cụ thể, thử lấy phần đầu của tiêu đề
            if not account_info["broker"] and "metatrader" in title.lower():
                parts = title.lower().split("metatrader")
                if parts and parts[0].strip():
                    account_info["broker"] = parts[0].strip()
                    print(f"  -> Tìm thấy broker (từ tiêu đề): {account_info['broker']}")
            
            # Dùng server làm broker nếu chưa có thông tin broker
            if not account_info["broker"] and account_info["server"]:
                account_info["broker"] = account_info["server"]
                print(f"  -> Dùng server làm broker: {account_info['broker']}")
            
            # Post-processing: Kiểm tra và loại bỏ các giá trị không hợp lệ
            
            # 1. Xác thực login ID
            if account_info["login_id"]:
                # Kiểm tra xem login_id có phải là một số hợp lệ không
                if not account_info["login_id"].isdigit() or len(account_info["login_id"]) < 5:
                    print(f"  -> Login ID không hợp lệ: {account_info['login_id']}")
                    account_info["login_id"] = ""
                # Trường hợp đặc biệt: Một số giá trị số phổ biến không phải ID (như năm, trạng thái, v.v.)
                invalid_ids = ["2023", "2024", "2022", "2021", "2020", "2019", "2018", "1234", "123456"]
                if account_info["login_id"] in invalid_ids:
                    print(f"  -> Login ID có vẻ là sai (từ khóa phổ biến): {account_info['login_id']}")
                    account_info["login_id"] = ""
            
            # 2. Xác thực server
            if account_info["server"]:
                # Kiểm tra xem server có hợp lệ không
                invalid_server_keywords = ["version", "v.", "preview", "windows", "microsoft", "update"]
                if any(keyword in account_info["server"].lower() for keyword in invalid_server_keywords):
                    print(f"  -> Server không hợp lệ: {account_info['server']}")
                    account_info["server"] = ""
            
            # 3. Xác thực broker
            if account_info["broker"]:
                # Kiểm tra xem broker có hợp lệ không
                invalid_broker_keywords = ["version", "v.", "preview", "windows", "microsoft", "update"]
                if any(keyword in account_info["broker"].lower() for keyword in invalid_broker_keywords):
                    print(f"  -> Broker không hợp lệ: {account_info['broker']}")
                    account_info["broker"] = ""
            
            # Loại bỏ các tài khoản không hợp lệ (không có đủ thông tin)
            if not account_info["login_id"] and not account_info["server"]:
                print(f"  => Cửa sổ này không thể xác định là tài khoản MT4/MT5 hợp lệ!")
                account_info = {"login_id": "", "broker": "", "server": ""}
            else:
                print(f"  => Kết quả phân tích: ID={account_info['login_id']}, Server={account_info['server']}, Broker={account_info['broker']}")
            
            return account_info
            
        except Exception as e:
            print(f"Lỗi khi trích xuất thông tin tài khoản: {str(e)}")
            return account_info

    def check_branches_in_sheet(self):
        """Kiểm tra tất cả các cột để tìm thông tin về nhánh trong bảng sheet"""
        if self.all_data is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng kết nối đến Google Sheet trước!")
            return
            
        try:
            # Lấy header row từ cấu hình
            try:
                header_row = int(self.header_row_input.text()) - 1
                if header_row < 0:
                    header_row = 0
            except ValueError:
                header_row = 0
                
            # In ra header để kiểm tra
            if len(self.all_data) > header_row:
                headers = self.all_data[header_row]
                print(f"Headers: {headers}")
                
                # In ra 5 hàng đầu tiên và toàn bộ dữ liệu của chúng để kiểm tra
                print("\n==== DỮ LIỆU MẪU TOÀN BỘ HÀNG ĐẦU TIÊN ====")
                for i, row in enumerate(self.all_data[header_row+1:header_row+6]):
                    print(f"Hàng {i+1}: {row}")
                print("\n==== KẾT THÚC DỮ LIỆU MẪU ====\n")
                
                # Tìm kiếm từ khóa "nhánh" trong tất cả các cột của mỗi hàng
                print("\n==== TÌM KIẾM THÔNG TIN NHÁNH TRONG TẤT CẢ CÁC CỘT ====")
                branch_keywords = ["nhánh", "branch", "chi nhánh"]
                branches_found = []
                
                for i, row in enumerate(self.all_data[header_row+1:header_row+100]):  # Chỉ kiểm tra 100 hàng đầu
                    for j, cell in enumerate(row):
                        if isinstance(cell, str) and any(keyword in cell.lower() for keyword in branch_keywords):
                            print(f"Hàng {i+1}, Cột {j+1} ('{headers[j] if j < len(headers) else 'N/A'}'): {cell}")
                            branches_found.append(cell)
                
                if not branches_found:
                    print("Không tìm thấy thông tin về nhánh trong 100 hàng đầu tiên.")
                else:
                    print("\nCác giá trị nhánh tìm thấy:")
                    for branch in set(branches_found):
                        print(f"- {branch}")
                        
                print("\n==== KẾT THÚC TÌM KIẾM THÔNG TIN NHÁNH ====")
                
                # Thông báo
                result_text = "Đã hoàn thành kiểm tra thông tin nhánh. Vui lòng xem kết quả trong console."
                self.data_display.setText(result_text)
                QMessageBox.information(self, "Hoàn thành", result_text)
                
        except Exception as e:
            error_msg = f"Lỗi khi kiểm tra thông tin nhánh: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Lỗi", error_msg)

    def check_branch_accounts(self):
        """Kiểm tra xem các tài khoản đang đăng nhập có thuộc đúng nhánh không và đề xuất đổi nếu sai"""
        if self.all_data is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng kết nối đến Google Sheet trước!")
            return
            
        # Lấy danh sách các nhánh từ dữ liệu
        branches = self.get_available_branches()
        
        if not branches:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy thông tin nhánh trong dữ liệu!")
            return
            
        # Hiển thị dialog để chọn nhánh
        branch, ok = QInputDialog.getItem(
            self, 
            "Chọn nhánh", 
            "Chọn nhánh để kiểm tra tài khoản:", 
            branches, 
            0, 
            False
        )
        
        if not ok or not branch:
            return
            
        # Tìm tất cả cửa sổ MT4/MT5 đang chạy
        self.data_display.setText(f"🔍 Đang kiểm tra các tài khoản đang đăng nhập có thuộc nhánh '{branch}' không...")
        QApplication.processEvents()
        
        try:
            # Khởi tạo COM
            try:
                pythoncom.CoInitialize()
                print("COM initialized for branch checking")
            except Exception as com_err:
                print(f"Warning: COM initialization error: {str(com_err)}")
            
            # Tìm tất cả cửa sổ MT4/MT5 đang chạy
            running_terminals = self.find_running_terminals()
            
            if not running_terminals:
                self.data_display.setText("❌ Không tìm thấy cửa sổ MT4/MT5 nào đang chạy!")
                return
            
            # Lọc ra các tài khoản thuộc nhánh đã chọn trong Google Sheet
            branch_accounts = self.get_branch_accounts(branch)
            
            if not branch_accounts:
                self.data_display.setText(f"❌ Không tìm thấy tài khoản nào thuộc nhánh '{branch}' trong bảng dữ liệu!")
                return
                
            # Kiểm tra từng cửa sổ MT4/MT5 đang chạy
            mismatched_accounts = []
            for terminal in running_terminals:
                login_id = terminal.get("login_id", "").strip()
                if not login_id:
                    continue  # Bỏ qua nếu không có login ID
                
                # Tìm thông tin tài khoản này trong bảng dữ liệu
                account_info = self.find_account_info(login_id)
                if not account_info:
                    continue  # Bỏ qua nếu không tìm thấy tài khoản trong dữ liệu
                
                # Kiểm tra xem tài khoản có thuộc nhánh đã chọn không
                account_branch = account_info.get("branch_name", "")
                if account_branch and account_branch.lower() != branch.lower():
                    # Thêm vào danh sách tài khoản không đúng nhánh
                    mismatched_accounts.append({
                        "login_id": login_id,
                        "broker": terminal.get("broker", ""),
                        "server": terminal.get("server", ""),
                        "platform": terminal.get("platform", ""),
                        "current_branch": account_branch,
                        "correct_branch": branch,
                        "title": terminal.get("title", "")
                    })
            
            # Hiển thị kết quả kiểm tra
            if not mismatched_accounts:
                self.data_display.setText(f"✅ Tất cả tài khoản đang đăng nhập đều thuộc nhánh '{branch}'!")
                return
                
            # Xử lý từng tài khoản không đúng nhánh
            self.process_mismatched_accounts(mismatched_accounts, branch, branch_accounts)
                
        except Exception as e:
            error_detail = f"Lỗi khi kiểm tra nhánh: {str(e)}\nLoại: {type(e).__name__}"
            self.data_display.setText(error_detail)
            print(error_detail)
            import traceback
            traceback.print_exc()
        finally:
            # Giải phóng COM
            try:
                pythoncom.CoUninitialize()
                print("COM uninitialized after branch checking")
            except:
                pass
    
    def get_available_branches(self):
        """Lấy danh sách các nhánh có trong dữ liệu"""
        if self.all_data is None:
            return []
        try:
            header_row = int(self.header_row_input.text()) - 1
            if header_row < 0:
                header_row = 0
        except Exception:
            header_row = 0
        note1_index = self.get_column_index(self.branch_col_input.text())
        branches = set()
        for row_data in self.all_data[header_row + 1:]:
            if len(row_data) > note1_index:
                note_value = str(row_data[note1_index]).strip()
                if note_value:
                    branch_name = self.extract_branch_name(note_value)
                    if branch_name:
                        branches.add(branch_name)
        return sorted(branches)
    
    def get_branch_accounts(self, branch):
        """Lấy danh sách các tài khoản thuộc nhánh đã chọn với End Equity > 100"""
        if self.all_data is None:
            return []
            
        branch_accounts = []
        
        try:
            # Lấy các thông số cấu hình
            try:
                header_row = int(self.header_row_input.text()) - 1
                if header_row < 0:
                    header_row = 0
            except ValueError:
                header_row = 0
                
            login_col_index = self.get_column_index(self.login_col_input.text())
            broker_col_index = self.get_column_index(self.broker_col_input.text())
            server_col_index = self.get_column_index(self.server_col_input.text())
            pass_col_index = self.get_column_index(self.pass_col_input.text())
            note1_index = self.get_column_index(self.branch_col_input.text())
            equity_col_index = 15  # Cột P - EndEquity (index 15)
            
            if login_col_index < 0 or broker_col_index < 0 or server_col_index < 0 or pass_col_index < 0 or note1_index < 0:
                print("Lỗi: Cấu hình cột không hợp lệ")
                return []
            
            # Tìm các tài khoản thuộc nhánh đã chọn
            for i, row_data in enumerate(self.all_data[header_row + 1:]):
                if len(row_data) <= max(login_col_index, broker_col_index, server_col_index, pass_col_index, note1_index, equity_col_index):
                    continue
                
                login_id = str(row_data[login_col_index]).strip()
                if not login_id:
                    continue
                
                # Lấy thông tin nhánh từ cột E (Note1)
                note_value = str(row_data[note1_index]).strip() if note1_index < len(row_data) else ""
                if not note_value:
                    continue
                
                # Kiểm tra xem tài khoản có thuộc nhánh đã chọn không
                account_branch = self.extract_branch_name(note_value)
                if account_branch.lower() != branch.lower():
                    continue
                
                # Lấy End Equity nếu có
                equity_value = 0
                try:
                    equity_str = str(row_data[equity_col_index]).strip()
                    if equity_str:
                        # Xử lý định dạng số kiểu Việt Nam/Châu Âu: 3.482,67 hoặc 3,482.67 hoặc 3.482.67
                        # Kiểm tra xem có phải dạng 3.482.67 không (dấu chấm phân cách hàng nghìn)
                        if equity_str.count('.') > 1:
                            # Loại bỏ tất cả dấu chấm trừ dấu chấm cuối cùng
                            last_dot = equity_str.rfind('.')
                            equity_str = equity_str.replace('.', '')
                            equity_str = equity_str[:last_dot] + '.' + equity_str[last_dot:]
                        else:
                            # Xử lý định dạng thông thường
                            equity_str = equity_str.replace(',', '.')
                        
                        # Chuyển thành số
                        equity_value = float(equity_str)
                except Exception as e:
                    print(f"Lỗi khi chuyển đổi End Equity cho tài khoản {login_id}: {str(e)}")
                    # Log để debug
                    print(f"Giá trị gốc: '{str(row_data[equity_col_index])}'")
                
                # Chỉ lấy các tài khoản có End Equity > 100
                if equity_value <= 100:
                    continue
                
                # Lấy các thông tin cần thiết
                broker_name = str(row_data[broker_col_index]).strip() if broker_col_index < len(row_data) else ""
                server_name = str(row_data[server_col_index]).strip() if server_col_index < len(row_data) else ""
                password = str(row_data[pass_col_index]).strip() if pass_col_index < len(row_data) else ""
                
                if not broker_name or not password:
                    continue
                
                # Thêm vào danh sách
                branch_accounts.append({
                    "login_id": login_id,
                    "broker": broker_name,
                    "server": server_name,
                    "password": password,
                    "branch": account_branch,
                    "equity": equity_value
                })
            
            # Sắp xếp theo End Equity giảm dần
            branch_accounts.sort(key=lambda x: x.get("equity", 0), reverse=True)
            
        except Exception as e:
            print(f"Lỗi khi lấy danh sách tài khoản theo nhánh: {str(e)}")
        
        return branch_accounts
    
    def find_account_info(self, login_id):
        """Tìm thông tin tài khoản trong bảng dữ liệu"""
        if self.all_data is None:
            return None
            
        try:
            # Lấy các thông số cấu hình
            try:
                header_row = int(self.header_row_input.text()) - 1
                if header_row < 0:
                    header_row = 0
            except ValueError:
                header_row = 0
                
            login_col_index = self.get_column_index(self.login_col_input.text())
            broker_col_index = self.get_column_index(self.broker_col_input.text())
            note1_index = self.get_column_index(self.branch_col_input.text())
            
            if login_col_index < 0 or broker_col_index < 0 or note1_index < 0:
                return None
            
            # Tìm tài khoản trong bảng dữ liệu
            for i, row_data in enumerate(self.all_data[header_row + 1:]):
                if len(row_data) <= max(login_col_index, broker_col_index, note1_index):
                    continue
                
                current_login_id = str(row_data[login_col_index]).strip()
                if current_login_id != login_id:
                    continue
                
                # Lấy thông tin nhánh từ cột E (Note1)
                note_value = str(row_data[note1_index]).strip() if note1_index < len(row_data) else ""
                branch_name = self.extract_branch_name(note_value)
                
                # Lấy thông tin sàn
                broker_name = str(row_data[broker_col_index]).strip() if broker_col_index < len(row_data) else ""
                
                return {
                    "login_id": login_id,
                    "broker": broker_name,
                    "branch_name": branch_name,
                    "note": note_value,
                    "row_data": row_data
                }
            
        except Exception as e:
            print(f"Lỗi khi tìm thông tin tài khoản {login_id}: {str(e)}")
        
        return None
    
    def extract_branch_name(self, note_value):
        """Trích xuất tên nhánh từ giá trị Note1"""
        if not note_value:
            return ""
            
        branch_name = ""
        note_value_lower = note_value.lower()
        
        # Danh sách các nhánh cụ thể để tìm kiếm
        specific_branches = [
            "nhánh a khang", "nhánh phát", "nhánh hoàng", "nhánh anh khang",
            "nhánh phú", "nhánh đạt", "nhánh đức", "nhánh tuấn", "nhánh tân",
            "nhánh hải", "nhánh hùng", "nhánh long", "nhánh quân", "nhánh minh",
            "nhánh thái", "nhánh thành", "nhánh son", "nhánh khánh", "nhánh khoa"
        ]
        
        # Kiểm tra xem note_value có chứa một trong các nhánh cụ thể không
        for specific_branch in specific_branches:
            if specific_branch in note_value_lower:
                branch_name = specific_branch
                break
        
        # Nếu không tìm thấy trong danh sách cụ thể, thử tìm theo từ khóa "nhánh"
        if not branch_name and "nhánh" in note_value_lower:
            parts = note_value_lower.split("nhánh")
            if len(parts) > 1:
                branch_name = "nhánh" + parts[1].strip()
        
        # Nếu vẫn không tìm thấy từ khóa nhánh, sử dụng toàn bộ giá trị note
        if not branch_name:
            branch_name = note_value
        
        return branch_name
    
    def process_mismatched_accounts(self, mismatched_accounts, target_branch, branch_accounts):
        """Xử lý các tài khoản không đúng nhánh"""
        if not mismatched_accounts:
            return
            
        # In thông tin debug để kiểm tra
        print(f"\n=== THÔNG TIN DEBUG KIỂM TRA NHÁNH ===")
        print(f"Số tài khoản không đúng nhánh: {len(mismatched_accounts)}")
        print(f"Số tài khoản đúng nhánh với End Equity > 100: {len(branch_accounts)}")
        print("\nCác tài khoản đúng nhánh có thể thay thế:")
        for i, acc in enumerate(branch_accounts[:5]):  # Hiển thị tối đa 5 tài khoản
            print(f"  {i+1}. Login: {acc['login_id']}, Broker: {acc['broker']}, Server: {acc['server']}, Equity: {acc['equity']}")
        if len(branch_accounts) > 5:
            print(f"  ... và {len(branch_accounts) - 5} tài khoản khác")
        print("\nCác tài khoản cần thay thế:")
        for i, acc in enumerate(mismatched_accounts):
            print(f"  {i+1}. Login: {acc['login_id']}, Broker: {acc['broker']}, Server: {acc['server']}, Nhánh hiện tại: {acc['current_branch']}")
        print("=====================================\n")
        
        # Hiển thị dialog chọn tài khoản để thay thế
        verification_dialog = BranchVerificationDialog(mismatched_accounts, target_branch, branch_accounts, self)
        
        if verification_dialog.exec_() != QDialog.Accepted:
            return  # Người dùng đã hủy
        
        # Lấy danh sách các tài khoản đã chọn để thay thế
        selected_accounts = verification_dialog.selected_accounts
        
        if not selected_accounts:
            self.data_display.setText("Không có tài khoản nào được chọn để thay thế.")
            return
        
        # Tải cấu hình tốc độ từ file
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mt_login_config.json")
        speed_settings = {
            "focus_delay": 0.1,
            "key_delay": 0.02,
            "form_open_delay": 0.2,
            "field_delay": 0.04
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "speed_settings" in config:
                        speed_settings = config["speed_settings"]
                        print(f"Đã tải cấu hình tốc độ từ file: {speed_settings}")
        except Exception as config_err:
            print(f"Không thể tải cấu hình tốc độ: {str(config_err)}")
            
        # Thực hiện đăng nhập cho các tài khoản đã chọn
        login_count = 0
        login_results = []
        
        for result in selected_accounts:
            if result["action"] == "login" and result["new_account"]:
                login_id = result["new_account"]["login_id"]
                password = result["new_account"]["password"]
                server = result["new_account"]["server"]
                broker = result["new_account"]["broker"]
                old_login_id = result["old_account"]["login_id"]
                
                # Lấy thông tin nền tảng từ tài khoản cũ
                platform_type = result["old_account"]["platform"]
                
                # Thêm thông tin vào kết quả
                login_result = {
                    "old_login_id": old_login_id,
                    "new_login_id": login_id,
                    "status": "pending",
                    "message": ""
                }
                login_results.append(login_result)
                
                # Thực hiện đăng nhập sử dụng phương thức có sẵn
                try:
                    # Tìm cửa sổ MT4/MT5 tương ứng
                    target_title = result["old_account"]["title"]
                    print(f"\nĐang thay đổi tài khoản: {old_login_id} -> {login_id}")
                    print(f"Tìm cửa sổ: {target_title}")
                    
                    # Khởi tạo COM
                    try:
                        pythoncom.CoInitialize()
                        print("COM initialized for login")
                    except Exception as com_err:
                        print(f"Warning: COM re-initialization error: {str(com_err)}")
                    
                    # Lấy danh sách cửa sổ
                    desktop = Desktop(backend="win32")
                    windows = desktop.windows()
                    
                    # Tìm cửa sổ tương ứng
                    target_window = None
                    for win in windows:
                        try:
                            if win.window_text() == target_title:
                                target_window = win
                                print(f"Tìm thấy cửa sổ: {target_title}")
                                break
                        except:
                            continue
                    
                    if target_window:
                        # Focus vào cửa sổ
                        try:
                            print("Đang focus vào cửa sổ...")
                            target_window.set_focus()
                        except Exception as focus_err:
                            print(f"Không thể focus cửa sổ: {str(focus_err)}")
                            try:
                                target_window.set_foreground()
                                print("Thử phương pháp set_foreground thay thế")
                            except Exception as e:
                                print(f"Cũng không thể set_foreground: {str(e)}")
                                try:
                                    # Thử phương pháp cuối cùng với pyautogui
                                    windows_with_title = pyautogui.getWindowsWithTitle(target_title)
                                    if windows_with_title:
                                        windows_with_title[0].activate()
                                        print("Đã kích hoạt cửa sổ bằng pyautogui")
                                except Exception as e2:
                                    print(f"Không thể kích hoạt cửa sổ: {str(e2)}")
                        
                        time.sleep(speed_settings["focus_delay"])
                        
                        # Thực hiện đăng nhập
                        # Mở form login
                        print("Đang mở form login...")
                        
                        # Nhấn Alt+F để mở menu File
                        pyautogui.keyDown('alt')
                        time.sleep(speed_settings["key_delay"])
                        pyautogui.press('f')
                        time.sleep(speed_settings["key_delay"])
                        pyautogui.keyUp('alt')
                        time.sleep(speed_settings["key_delay"])
                        
                        # Nhấn L để chọn Login
                        pyautogui.press('l')
                        time.sleep(speed_settings["form_open_delay"])  # Đợi form login hiện lên
                        
                        # Điền thông tin login
                        print(f"Đang điền form login cho tài khoản {login_id}...")
                        
                        # Điền Login ID
                        print("Đã điền Login ID: " + login_id)
                        pyperclip.copy(str(login_id).strip())
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(speed_settings["field_delay"])
                        pyautogui.press('tab')
                        time.sleep(speed_settings["field_delay"])
                        
                        # Điền Password
                        print("Đã điền Password: " + "*" * len(password))
                        pyperclip.copy(str(password).strip())
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(speed_settings["field_delay"])
                        pyautogui.press('tab')
                        time.sleep(speed_settings["field_delay"])
                        
                        # Điền Server (nếu trường hợp đặc biệt cho MT5)
                        if platform_type == "MT5":
                            # MT5: Nhấn thêm Tab một lần nữa trước khi điền Server
                            pyautogui.press('tab')
                            time.sleep(speed_settings["field_delay"])
                        
                        # Điền Server name nếu có
                        if server:
                            print("Đang điền server: " + server)
                            pyperclip.copy(str(server).strip())
                            pyautogui.hotkey('ctrl', 'v')
                            time.sleep(speed_settings["field_delay"])
                        
                        # Di chuyển đến nút OK
                        print("Di chuyển đến nút OK...")
                        if platform_type == "MT4":
                            # MT4: Tab 2 lần để focus vào nút OK
                            pyautogui.press('tab')
                            time.sleep(speed_settings["key_delay"])
                            pyautogui.press('tab')
                            time.sleep(speed_settings["key_delay"])
                        else:
                            # MT5: Chỉ cần Tab 1 lần nữa
                            pyautogui.press('tab')
                            time.sleep(speed_settings["key_delay"])
                        
                        # Nhấn Enter để submit
                        print("Nhấn Enter để đăng nhập...")
                        pyautogui.press('enter')
                        time.sleep(speed_settings["form_open_delay"]) # Đợi sau khi nhấn submit
                        
                        login_result["status"] = "success"
                        login_result["message"] = f"✅ Đăng nhập thành công tài khoản: {login_id}"
                        login_count += 1
                        print(login_result["message"])
                    else:
                        login_result["status"] = "failed"
                        login_result["message"] = f"❌ Không tìm thấy cửa sổ cho tài khoản {old_login_id}"
                        print(login_result["message"])
                except Exception as login_err:
                    login_result["status"] = "failed"
                    login_result["message"] = f"❌ Lỗi khi đăng nhập tài khoản {login_id}: {str(login_err)}"
                    print(login_result["message"])
                        
        # Hiển thị kết quả
        if login_count > 0:
            summary = f"Đã đăng nhập thành công {login_count}/{len(selected_accounts)} tài khoản.\n\n"
            for result in login_results:
                summary += f"{result['message']}\n"
            self.data_display.setText(summary)
        else:
            self.data_display.setText("Không thể đăng nhập tài khoản nào. Vui lòng kiểm tra lại thông tin.")

    def check_low_equity_accounts(self):
        """Kiểm tra các tài khoản đang mở trên máy có EndEquity < 100 và gợi ý tài khoản khác cùng sàn, hiển thị lên dialog riêng"""
        if self.df is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng kết nối đến Google Sheet trước!")
            return
        QApplication.processEvents()
        try:
            try:
                pythoncom.CoInitialize()
            except Exception as com_err:
                print(f"Warning: COM initialization error: {str(com_err)}")
            running_terminals = self.find_running_terminals()
            if not running_terminals:
                running_terminals = self.find_mt_windows_alternative()
            login_col_index = self.get_column_index(self.login_col_input.text())
            broker_col_index = self.get_column_index(self.broker_col_input.text())
            server_col_index = self.get_column_index(self.server_col_input.text())
            name_col_index = 2  # Cột tên tài khoản (thường là C)
            equity_col_index = 15  # Cột P - EndEquity (index 15)
            header_row = 0
            try:
                header_row = int(self.header_row_input.text()) - 1
                if header_row < 0:
                    header_row = 0
            except ValueError:
                header_row = 0
            low_equity_accounts = []
            # Tạo set chứa tất cả login_id trong sheet để kiểm tra tồn tại
            all_login_ids_in_sheet = set()
            for row_data in self.all_data[header_row + 1:]:
                if len(row_data) > login_col_index:
                    all_login_ids_in_sheet.add(str(row_data[login_col_index]).strip())
            # Quét từng terminal đang mở
            for terminal in running_terminals:
                login_id = terminal.get("login_id", "").strip()
                if not login_id:
                    continue
                found_in_sheet = False
                for row_data in self.all_data[header_row + 1:]:
                    if len(row_data) <= max(login_col_index, broker_col_index, server_col_index, name_col_index, equity_col_index):
                        continue
                    sheet_login_id = str(row_data[login_col_index]).strip()
                    if sheet_login_id == login_id:
                        found_in_sheet = True
                        try:
                            equity_str = str(row_data[equity_col_index]).strip()
                            equity_value = 0
                            if equity_str:
                                if equity_str.count('.') > 1:
                                    last_dot = equity_str.rfind('.')
                                    equity_str = equity_str.replace('.', '')
                                    equity_str = equity_str[:last_dot] + '.' + equity_str[last_dot:]
                                else:
                                    equity_str = equity_str.replace(',', '.')
                                equity_value = float(equity_str)
                        except Exception as e:
                            equity_value = 0
                        if equity_value < 100:
                            broker = str(row_data[broker_col_index]).strip()
                            server = str(row_data[server_col_index]).strip()
                            name = str(row_data[name_col_index]).strip() if name_col_index < len(row_data) else ""
                            low_equity_accounts.append({
                                "login_id": login_id,
                                "broker": broker,
                                "server": server,
                                "name": name,
                                "equity": equity_value,
                                "window_title": terminal.get("title", ""),
                                "platform": terminal.get("platform", ""),
                                "reason": "Hết tiền"
                            })
                        break
                if not found_in_sheet:
                    # Tài khoản không tồn tại trong sheet
                    low_equity_accounts.append({
                        "login_id": login_id,
                        "broker": terminal.get("broker", ""),
                        "server": terminal.get("server", ""),
                        "name": "",
                        "equity": 0,
                        "window_title": terminal.get("title", ""),
                        "platform": terminal.get("platform", ""),
                        "reason": "Không tồn tại trong sheet"
                    })
            if not low_equity_accounts:
                QMessageBox.information(self, "Kết quả", "Không có tài khoản nào hết tiền (EndEquity < 100) hoặc không tồn tại trong sheet trên các sàn đang mở!")
                return
            self.low_equity_accounts_data = low_equity_accounts
            dlg = LowEquityDialog(self)
            dlg.set_accounts(low_equity_accounts)
            dlg.exec_()
        except Exception as e:
            error_detail = f"Lỗi khi kiểm tra tài khoản hết tiền: {str(e)}\nLoại: {type(e).__name__}"
            QMessageBox.critical(self, "Lỗi", error_detail)
            print(error_detail)
            import traceback
            traceback.print_exc()
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def login_suggestion_to_window(self, acc, suggestion):
        """Đăng nhập tài khoản suggestion vào cửa sổ acc (acc là tài khoản hết tiền) với tốc độ nhanh như các chức năng đăng nhập khác"""
        try:
            pythoncom.CoInitialize()
        except:
            pass
        try:
            # Tìm cửa sổ theo tiêu đề và nền tảng
            desktop = Desktop(backend="win32")
            windows = desktop.windows()
            target_window = None
            for win in windows:
                try:
                    if win.window_text() == acc["window_title"]:
                        target_window = win
                        break
                except:
                    continue
            if not target_window:
                print(f"Không tìm thấy cửa sổ cho: {acc['window_title']}")
                return
            # Focus vào cửa sổ
            try:
                target_window.set_focus()
            except:
                try:
                    target_window.set_foreground()
                except:
                    pass
            # Tăng tốc độ đăng nhập (giảm delay)
            focus_delay = 0.1
            key_delay = 0.02
            form_open_delay = 0.2
            field_delay = 0.04
            import time
            time.sleep(focus_delay)
            # Mở form login
            pyautogui.keyDown('alt')
            time.sleep(key_delay)
            pyautogui.press('f')
            time.sleep(key_delay)
            pyautogui.keyUp('alt')
            time.sleep(key_delay)
            pyautogui.press('l')
            time.sleep(form_open_delay)
            # Điền Login ID
            pyperclip.copy(str(suggestion['login_id']).strip())
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(field_delay)
            pyautogui.press('tab')
            time.sleep(field_delay)
            # Điền Password
            pyperclip.copy(str(suggestion['password']).strip())
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(field_delay)
            pyautogui.press('tab')
            time.sleep(field_delay)
            # MT5 cần tab thêm 1 lần trước khi điền server
            if acc['platform'] == 'MT5':
                pyautogui.press('tab')
                time.sleep(field_delay)
            # Điền Server
            pyperclip.copy(str(suggestion['server']).strip())
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(field_delay)
            # Tab đến nút OK
            if acc['platform'] == 'MT4':
                pyautogui.press('tab')
                time.sleep(key_delay)
                pyautogui.press('tab')
                time.sleep(key_delay)
            else:
                pyautogui.press('tab')
                time.sleep(key_delay)
            # Nhấn Enter để đăng nhập
            pyautogui.press('enter')
            time.sleep(form_open_delay)
        except Exception as e:
            print(f"Lỗi khi đăng nhập tài khoản gợi ý: {str(e)}")
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def goto_home_tab(self):
        """Chuyển về tab Quản lý tài khoản"""
        self.tab_widget.setCurrentWidget(self.main_tab)

    def search_accounts(self):
        """Tìm kiếm tài khoản theo Tên Sàn (cột cấu hình broker_col) hoặc Login ID (cột cấu hình login_col) và hiển thị kết quả trong bảng"""
        if self.df is None:
            return
        keyword = self.search_input.text().strip().lower()
        if not keyword:
            self.apply_filters()
            return
        # Xác định tên cột thực tế trong DataFrame dựa trên cấu hình
        broker_col_letter = self.broker_col_input.text().strip().upper()
        login_col_letter = self.login_col_input.text().strip().upper()
        # Lấy header từ Google Sheet (sau khi đã xử lý trùng lặp)
        headers = list(self.df.columns)
        # Tìm tên cột tương ứng với broker_col và login_col
        broker_col_name = None
        login_col_name = None
        # Lấy header row từ cấu hình
        try:
            header_row = int(self.header_row_input.text())
            if header_row < 1:
                header_row = 1
        except ValueError:
            header_row = 1
        # Lấy lại header gốc từ all_data nếu có
        if self.all_data and len(self.all_data) >= header_row:
            sheet_headers = self.all_data[header_row - 1]
            start_col = 2
            end_col = 14
            end_col = min(end_col, len(sheet_headers) - 1)
            selected_headers = sheet_headers[start_col:end_col + 1]
            unique_headers = []
            header_count = {}
            for header in selected_headers:
                if not header:
                    header = "Column"
                if header in header_count:
                    header_count[header] += 1
                    unique_headers.append(f"{header}_{header_count[header]}")
                else:
                    header_count[header] = 0
                    unique_headers.append(header)
            # Ánh xạ vị trí cột cấu hình sang tên header thực tế
            col_map = {chr(65 + i): i for i in range(len(sheet_headers))}
            broker_idx = col_map.get(broker_col_letter, None)
            login_idx = col_map.get(login_col_letter, None)
            if broker_idx is not None and broker_idx >= start_col and broker_idx <= end_col:
                broker_col_name = unique_headers[broker_idx - start_col]
            if login_idx is not None and login_idx >= start_col and login_idx <= end_col:
                login_col_name = unique_headers[login_idx - start_col]
        # Nếu không tìm được thì fallback về tìm theo tên gần đúng
        search_cols = []
        if broker_col_name and broker_col_name in headers:
            search_cols.append(broker_col_name)
        if login_col_name and login_col_name in headers:
            search_cols.append(login_col_name)
        if not search_cols:
            self.data_display.setText("❌ Không tìm thấy cột Tên Sàn hoặc Login ID trong dữ liệu! Kiểm tra lại cấu hình cột và tiêu đề sheet.")
            self.display_filtered_data(self.df.iloc[0:0])
            return
        self.data_display.setText(f"Đang tìm kiếm trên các cột: {', '.join(search_cols)}")
        def row_match(row):
            for col in search_cols:
                if keyword in str(row.get(col, "")).lower():
                    return True
            return False
        filtered_df = self.df[self.df.apply(row_match, axis=1)]
        if filtered_df.empty:
            self.data_display.append("❌ Không tìm thấy tài khoản nào phù hợp với từ khóa bạn nhập!")
        self.display_filtered_data(filtered_df)

    def clear_search(self):
        """Xóa tìm kiếm và hiển thị lại toàn bộ dữ liệu"""
        self.search_input.clear()
        self.apply_filters()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Cài đặt")
        
        # Sử dụng kích thước tương đối so với màn hình
        screen_rect = QApplication.desktop().availableGeometry()
        width = int(screen_rect.width() * 0.4)  # 70% chiều rộng màn hình
        height = int(screen_rect.height() * 0.7)  # 70% chiều cao màn hình
        self.setGeometry(
            (screen_rect.width() - width) // 2,  # Căn giữa theo chiều ngang
            (screen_rect.height() - height) // 2,  # Căn giữa theo chiều dọc
            width, 
            height
        )
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Group Box cho Credentials
        creds_group = QGroupBox("Google Sheets Credentials")
        creds_layout = QVBoxLayout()
        creds_group.setLayout(creds_layout)
        
        # Hiển thị đường dẫn credentials.json
        creds_file_layout = QHBoxLayout()
        creds_label = QLabel(f"Đang sử dụng credentials.json: {self.parent.credentials_path}")
        creds_file_layout.addWidget(creds_label)
        creds_layout.addLayout(creds_file_layout)
        
        # Layout cho URL Google Sheet
        sheet_url_layout = QHBoxLayout()
        self.sheet_url_input = QLineEdit()
        self.sheet_url_input.setPlaceholderText("URL của Google Sheet")
        self.sheet_url_input.setText(self.parent.sheet_url_input.text())
        
        sheet_url_layout.addWidget(QLabel("Sheet URL:"))
        sheet_url_layout.addWidget(self.sheet_url_input)
        creds_layout.addLayout(sheet_url_layout)
        
        # Layout cho tên worksheet
        worksheet_layout = QHBoxLayout()
        self.worksheet_input = QLineEdit()
        self.worksheet_input.setPlaceholderText("Tên của Sheet (mặc định là Sheet1)")
        self.worksheet_input.setText(self.parent.worksheet_input.text())
        
        worksheet_layout.addWidget(QLabel("Worksheet:"))
        worksheet_layout.addWidget(self.worksheet_input)
        creds_layout.addLayout(worksheet_layout)
        
        # Layout cho hàng tiêu đề (header row)
        header_row_layout = QHBoxLayout()
        self.header_row_input = QLineEdit()
        self.header_row_input.setPlaceholderText("Hàng tiêu đề (mặc định là 1)")
        self.header_row_input.setText(self.parent.header_row_input.text())
        
        header_row_layout.addWidget(QLabel("Hàng tiêu đề:"))
        header_row_layout.addWidget(self.header_row_input)
        creds_layout.addLayout(header_row_layout)
        
        layout.addWidget(creds_group)
        
        # Group Box cho cấu hình cột dữ liệu
        column_config_group = QGroupBox("Cấu hình cột dữ liệu")
        column_config_layout = QVBoxLayout()
        column_config_group.setLayout(column_config_layout)
        
        # Layout cho cấu hình cột Broker/Sàn
        broker_col_layout = QHBoxLayout()
        self.broker_col_input = QLineEdit()
        self.broker_col_input.setPlaceholderText("Cột chứa tên sàn (ví dụ: F)")
        self.broker_col_input.setText(self.parent.broker_col_input.text())
        
        broker_col_layout.addWidget(QLabel("Cột tên sàn:"))
        broker_col_layout.addWidget(self.broker_col_input)
        column_config_layout.addLayout(broker_col_layout)
        
        # Layout cho cấu hình cột Server
        server_col_layout = QHBoxLayout()
        self.server_col_input = QLineEdit()
        self.server_col_input.setPlaceholderText("Cột chứa tên server (ví dụ: D)")
        self.server_col_input.setText(self.parent.server_col_input.text())
        
        server_col_layout.addWidget(QLabel("Cột Name Server:"))
        server_col_layout.addWidget(self.server_col_input)
        column_config_layout.addLayout(server_col_layout)
        
        # Layout cho cấu hình cột Login ID
        login_col_layout = QHBoxLayout()
        self.login_col_input = QLineEdit()
        self.login_col_input.setPlaceholderText("Cột chứa Login ID (ví dụ: G)")
        self.login_col_input.setText(self.parent.login_col_input.text())
        
        login_col_layout.addWidget(QLabel("Cột Login ID:"))
        login_col_layout.addWidget(self.login_col_input)
        column_config_layout.addLayout(login_col_layout)
        
        # Layout cho cấu hình cột Password
        pass_col_layout = QHBoxLayout()
        self.pass_col_input = QLineEdit()
        self.pass_col_input.setPlaceholderText("Cột chứa Password (ví dụ: I)")
        self.pass_col_input.setText(self.parent.pass_col_input.text())
        
        pass_col_layout.addWidget(QLabel("Cột Password:"))
        pass_col_layout.addWidget(self.pass_col_input)
        column_config_layout.addLayout(pass_col_layout)
        
        # Layout cho cấu hình cột nhánh
        branch_col_layout = QHBoxLayout()
        self.branch_col_input = QLineEdit()
        self.branch_col_input.setPlaceholderText("Cột chứa thông tin nhánh (ví dụ: E)")
        self.branch_col_input.setText(self.parent.branch_col_input.text())
        branch_col_layout.addWidget(QLabel("Cột Nhánh:"))
        branch_col_layout.addWidget(self.branch_col_input)
        column_config_layout.addLayout(branch_col_layout)
        
        layout.addWidget(column_config_group)
        
        # Nút lưu và hủy
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def accept(self):
        # Chuyển dữ liệu từ dialog sang main window
        self.parent.sheet_url_input.setText(self.sheet_url_input.text())
        self.parent.worksheet_input.setText(self.worksheet_input.text())
        self.parent.header_row_input.setText(self.header_row_input.text())
        self.parent.broker_col_input.setText(self.broker_col_input.text())
        self.parent.server_col_input.setText(self.server_col_input.text())
        self.parent.login_col_input.setText(self.login_col_input.text())
        self.parent.pass_col_input.setText(self.pass_col_input.text())
        self.parent.branch_col_input.setText(self.branch_col_input.text())
        
        # Lưu cấu hình
        self.parent.save_config()
        super().accept()

class BranchVerificationDialog(QDialog):
    """Dialog hiển thị kết quả kiểm tra nhánh và cho phép chọn tài khoản để thay thế"""
    
    def __init__(self, mismatched_accounts, target_branch, branch_accounts, parent=None):
        super().__init__(parent)
        self.mismatched_accounts = mismatched_accounts
        self.target_branch = target_branch
        self.branch_accounts = branch_accounts
        self.replacement_map = {}  # Lưu các tài khoản đã tìm thấy để thay thế
        self.selected_accounts = []  # Lưu các tài khoản đã chọn để thay thế
        self.replacement_combos = {}  # Lưu các combobox cho từng dòng
        
        self.setWindowTitle(f"Kiểm tra tài khoản theo nhánh: {target_branch}")
        
        # Sử dụng kích thước tương đối so với màn hình
        screen_rect = QApplication.desktop().availableGeometry()
        width = int(screen_rect.width() * 0.7)  # Giảm chiều rộng xuống 40% màn hình
        height = int(screen_rect.height() * 0.7)  # Giữ nguyên chiều cao 70% màn hình
        self.setGeometry(
            (screen_rect.width() - width) // 2,  # Căn giữa theo chiều ngang
            (screen_rect.height() - height) // 2,  # Căn giữa theo chiều dọc
            width, 
            height
        )
        
        # Thiết lập cờ để ngăn việc thay đổi kích thước cửa sổ
        self.setFixedSize(width, height)
        
        self.setup_ui()
        self.find_replacements()
        self.populate_table()
        
        # Tự động chọn tất cả các tài khoản có tài khoản thay thế mặc định
        self.select_all_checkbox.setChecked(True)  # Đảm bảo checkbox chọn tất cả được chọn mặc định
    
    def setup_ui(self):
        """Thiết lập giao diện dialog"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Thông tin tổng quan
        info_label = QLabel(f"<b>Kết quả kiểm tra tài khoản theo nhánh: <span style='color:blue'>{self.target_branch}</span></b>")
        main_layout.addWidget(info_label)
        
        stats_label = QLabel(f"Tìm thấy <b>{len(self.mismatched_accounts)}</b> tài khoản không đúng nhánh và <b>{len(self.branch_accounts)}</b> tài khoản thuộc nhánh {self.target_branch} với End Equity > 100")
        main_layout.addWidget(stats_label)
        
        # Thông tin về cách sử dụng ComboBox
        combo_info = QLabel("<span style='color:#2196F3; font-weight:bold;'>🔄 CHÚ Ý:</span> Bạn có thể chọn tài khoản thay thế cụ thể bằng cách click vào ô ComboBox trong cột 'Tài khoản thay thế'")
        combo_info.setStyleSheet("background-color: #E3F2FD; padding: 5px; border-radius: 3px;")
        main_layout.addWidget(combo_info)
        
        # Bảng hiển thị tài khoản cần thay thế
        table_label = QLabel("<b>Danh sách tài khoản không đúng nhánh:</b>")
        main_layout.addWidget(table_label)
        
        self.accounts_table = QTableWidget()
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.setColumnCount(8)
        self.accounts_table.setHorizontalHeaderLabels([
            "Chọn", "Login ID", "Broker/Sàn", "Server", "Nền tảng", 
            "Nhánh hiện tại", "Tài khoản thay thế", "End Equity"
        ])
        
        # Thiết lập chiều rộng cột
        header = self.accounts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Cột checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Login ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Broker
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Server
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Platform
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Current branch
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Replacement - Đặt Stretch để ComboBox hiển thị đầy đủ
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Equity
        
        main_layout.addWidget(self.accounts_table)
        
        # Checkbox chọn tất cả
        self.select_all_checkbox = QCheckBox("Chọn tất cả tài khoản có tài khoản thay thế")
        self.select_all_checkbox.toggled.connect(self.toggle_all_rows)
        main_layout.addWidget(self.select_all_checkbox)
        
        # Thông tin
        info_text = QLabel("""
        <b>Lưu ý:</b>
        - Chọn các tài khoản bạn muốn thay thế sang tài khoản đúng nhánh
        - Các tài khoản có nhiều lựa chọn thay thế sẽ hiển thị danh sách thả xuống (ComboBox) để chọn
        - Hệ thống tự động tìm tài khoản thay thế phù hợp nhất dựa trên broker/server và End Equity
        - Chỉ hiển thị tài khoản thay thế có End Equity > 100
        - Khi bạn chọn tài khoản khác từ danh sách, giá trị Equity sẽ được cập nhật tương ứng
        """)
        main_layout.addWidget(info_text)
        
        # Các nút
        buttons_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Đăng nhập tài khoản đã chọn")
        self.login_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;")
        self.login_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Hủy")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(cancel_button)
        
        main_layout.addLayout(buttons_layout)
    
    def find_replacements(self):
        """Tìm tài khoản thay thế phù hợp cho mỗi tài khoản không đúng nhánh"""
        for account in self.mismatched_accounts:
            login_id = account["login_id"]
            broker = account.get("broker", "")
            server = account.get("server", "")
            
            # Bỏ qua nếu broker hoặc server không có giá trị
            if not broker or not server:
                self.replacement_map[login_id] = []
                continue
                
            # Chuẩn hóa broker và server để so sánh
            broker_normalized = broker.lower().strip()
            
            # Tách tên server theo yêu cầu: lấy phần trước dấu gạch ngang đầu tiên
            # Ví dụ: MarketEquityInc-Live sẽ lấy MarketEquityInc
            try:
                if "-" in server:
                    server_parts = server.split('-')
                    base_server = server_parts[0].strip()
                else:
                    # Nếu không có dấu gạch ngang, sử dụng toàn bộ tên server
                    base_server = server.strip()
                server_normalized = base_server.lower()
                
                print(f"Tìm kiếm cho tài khoản {login_id}: Server gốc = {server}, Server đã tách = {base_server}")
            except Exception as e:
                print(f"Lỗi khi tách server cho tài khoản {login_id}: {str(e)}")
                base_server = server.strip()
                server_normalized = base_server.lower()
            
            # Tìm tài khoản phù hợp để thay thế
            matching_accounts = []
            
            print(f"--- Bắt đầu tìm tài khoản thay thế cho {login_id} - Broker: {broker}, Server base: {base_server} ---")
            
            # Chỉ tìm khớp server, không cần khớp broker
            for branch_acc in self.branch_accounts:
                branch_broker = branch_acc["broker"].lower().strip()
                branch_server = branch_acc["server"].lower().strip()
                branch_login = branch_acc.get("login_id", "")
                branch_equity = branch_acc.get("equity", 0)
                
                # Tách tên server của tài khoản nhánh theo cùng quy tắc
                try:
                    if "-" in branch_acc["server"]:
                        branch_server_parts = branch_acc["server"].split('-')
                        branch_base_server = branch_server_parts[0].strip()
                    else:
                        # Nếu không có dấu gạch ngang, sử dụng toàn bộ tên server
                        branch_base_server = branch_acc["server"].strip()
                    branch_server_normalized = branch_base_server.lower()
                except Exception as e:
                    print(f"Lỗi khi tách server cho tài khoản nhánh: {str(e)}")
                    branch_base_server = branch_acc["server"].strip()
                    branch_server_normalized = branch_base_server.lower()
                
                # So sánh broker và server base
                broker_match = (broker_normalized in branch_broker or branch_broker in broker_normalized)
                server_match = (server_normalized in branch_server_normalized or branch_server_normalized in server_normalized)
                
                # Log kết quả so sánh cho debugging
                if server_match:
                    print(f"  Checking: {branch_login} - Broker: {branch_acc['broker']}, Server: {branch_acc['server']}, Base server: {branch_base_server}")
                    print(f"    Broker match: {broker_match} (Source: '{broker}' vs Branch: '{branch_acc['broker']}')")
                    print(f"    Server match: {server_match} (Source base: '{base_server}' vs Branch base: '{branch_base_server}')")
                    print(f"    Equity: {branch_equity}")
                
                # Chỉ yêu cầu server_match, không cần broker_match
                if server_match:
                    # Chỉ thêm vào danh sách nếu equity > 100
                    if branch_equity > 100:
                        matching_accounts.append(branch_acc)
                        print(f"    ✅ SERVER MATCH FOUND: {branch_login} - Equity: {branch_equity}")
                    else:
                        print(f"    ❌ EQUITY TOO LOW: {branch_login} - Equity: {branch_equity}")
            
            # Nếu không có tài khoản nào khớp server, thử tìm theo broker
            if not matching_accounts:
                print(f"  Không tìm thấy kết quả khớp server, tìm theo broker...")
                for branch_acc in self.branch_accounts:
                    branch_broker = branch_acc["broker"].lower().strip()
                    branch_login = branch_acc.get("login_id", "")
                    branch_equity = branch_acc.get("equity", 0)
                    
                    # So sánh chuỗi con cho broker
                    broker_match = (broker_normalized in branch_broker or branch_broker in broker_normalized)
                    
                    if broker_match:
                        print(f"  Checking broker only: {branch_login} - Broker: {branch_acc['broker']}")
                        print(f"    Equity: {branch_equity}")
                        
                        # Chỉ thêm vào danh sách nếu equity > 100
                        if branch_equity > 100:
                            matching_accounts.append(branch_acc)
                            print(f"    ✅ BROKER MATCH: {branch_login} - Equity: {branch_equity}")
                        else:
                            print(f"    ❌ EQUITY TOO LOW: {branch_login} - Equity: {branch_equity}")
            
            # Sắp xếp theo End Equity giảm dần
            matching_accounts.sort(key=lambda x: x.get("equity", 0), reverse=True)
            
            print(f"--- Kết quả tìm kiếm cho {login_id}: Tìm thấy {len(matching_accounts)} tài khoản phù hợp ---")
            
            # Lưu vào replacement_map
            self.replacement_map[login_id] = matching_accounts
    
    def populate_table(self):
        """Điền dữ liệu vào bảng"""
        # Thiết lập số hàng
        self.accounts_table.setRowCount(len(self.mismatched_accounts))
        for row, account in enumerate(self.mismatched_accounts):
            login_id = account["login_id"]
            current_branch = account.get("current_branch", "")
            broker = account.get("broker", "")
            server = account.get("server", "")
            platform = account.get("platform", "")
            # Checkbox để chọn tài khoản
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.accounts_table.setItem(row, 0, checkbox_item)
            # Login ID
            login_item = QTableWidgetItem(login_id)
            login_item.setFlags(login_item.flags() & ~Qt.ItemIsEditable)
            self.accounts_table.setItem(row, 1, login_item)
            # Broker
            broker_item = QTableWidgetItem(broker)
            broker_item.setFlags(broker_item.flags() & ~Qt.ItemIsEditable)
            self.accounts_table.setItem(row, 2, broker_item)
            # Server
            server_item = QTableWidgetItem(server)
            server_item.setFlags(server_item.flags() & ~Qt.ItemIsEditable)
            self.accounts_table.setItem(row, 3, server_item)
            # Platform
            platform_item = QTableWidgetItem(platform)
            platform_item.setFlags(platform_item.flags() & ~Qt.ItemIsEditable)
            self.accounts_table.setItem(row, 4, platform_item)
            # Current branch
            branch_item = QTableWidgetItem(current_branch)
            branch_item.setFlags(branch_item.flags() & ~Qt.ItemIsEditable)
            branch_item.setBackground(QColor(255, 200, 200))  # Light red background
            self.accounts_table.setItem(row, 5, branch_item)
            # Replacement account - giữ nguyên logic cũ
            matching_accounts = self.replacement_map.get(login_id, [])
            if matching_accounts:
                if len(matching_accounts) > 1:
                    combo = QComboBox()
                    for acc in matching_accounts:
                        account_text = f"{acc['login_id']} - {acc['broker']} - Equity: {acc['equity']:.2f}"
                        combo.addItem(account_text, acc)
                    self.replacement_combos[login_id] = combo
                    self.accounts_table.setCellWidget(row, 6, combo)
                    checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    equity_item = QTableWidgetItem(f"{matching_accounts[0]['equity']:.2f}")
                    equity_item.setFlags(equity_item.flags() & ~Qt.ItemIsEditable)
                    equity_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.accounts_table.setItem(row, 7, equity_item)
                    from functools import partial
                    combo.currentIndexChanged.connect(partial(self.update_equity_for_row, row, combo))
                else:
                    replacement = matching_accounts[0]
                    replacement_text = f"{replacement['login_id']} - {replacement['broker']} - Equity: {replacement['equity']:.2f}"
                    replacement_item = QTableWidgetItem(replacement_text)
                    replacement_item.setFlags(replacement_item.flags() & ~Qt.ItemIsEditable)
                    replacement_item.setBackground(QColor(200, 255, 200))
                    self.accounts_table.setItem(row, 6, replacement_item)
                    checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    equity_item = QTableWidgetItem(f"{replacement['equity']:.2f}")
                    equity_item.setFlags(equity_item.flags() & ~Qt.ItemIsEditable)
                    equity_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.accounts_table.setItem(row, 7, equity_item)
            else:
                replacement_item = QTableWidgetItem("Không tìm thấy")
                replacement_item.setFlags(replacement_item.flags() & ~Qt.ItemIsEditable)
                replacement_item.setForeground(QColor(255, 0, 0))
                self.accounts_table.setItem(row, 6, replacement_item)
                checkbox_item.setFlags(Qt.NoItemFlags)
                equity_item = QTableWidgetItem("")
                equity_item.setFlags(equity_item.flags() & ~Qt.ItemIsEditable)
                self.accounts_table.setItem(row, 7, equity_item)
        self.accounts_table.setColumnWidth(0, 50)
        header = self.accounts_table.horizontalHeader()
        for col in range(1, 8):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
    
    def update_equity_for_row(self, row, combo, index=None):
        """Cập nhật giá trị Equity khi chọn tài khoản khác từ combobox"""
        try:
            # Bắt lỗi nếu combo bị xóa
            selected_index = combo.currentIndex()
            selected_account = combo.itemData(selected_index)
            
            if selected_account:
                # Cập nhật ô Equity
                equity_item = QTableWidgetItem(f"{selected_account['equity']:.2f}")
                equity_item.setFlags(equity_item.flags() & ~Qt.ItemIsEditable)
                equity_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # Highlight giá trị Equity mới
                if selected_account['equity'] > 500:
                    # Equity cao (>500) - highlight xanh đậm
                    equity_item.setBackground(QColor(200, 255, 200))
                elif selected_account['equity'] > 300:
                    # Equity trung bình (300-500) - highlight xanh nhạt
                    equity_item.setBackground(QColor(220, 255, 220))
                elif selected_account['equity'] > 100:
                    # Equity thấp (100-300) - highlight vàng nhạt
                    equity_item.setBackground(QColor(255, 255, 200))
                
                self.accounts_table.setItem(row, 7, equity_item)
                
                # Cập nhật font cho hiển thị rõ hơn
                font = equity_item.font()
                font.setBold(True)
                equity_item.setFont(font)
                
                print(f"Đã cập nhật Equity cho dòng {row+1}: {selected_account['equity']:.2f}")
                
                # Làm nổi bật ComboBox bằng cách thay đổi stylesheet
                combo.setStyleSheet("background-color: #e6ffe6; border: 1px solid #4CAF50;")
                
                # Sử dụng QTimer để khôi phục stylesheet sau 500ms
                timer = QTimer(self)
                timer.setSingleShot(True)
                timer.timeout.connect(lambda: combo.setStyleSheet(""))
                timer.start(500)
        except Exception as e:
            print(f"Lỗi khi cập nhật Equity: {str(e)}")
            # Không làm gì nếu có lỗi
    
    def toggle_all_rows(self, checked):
        """Chọn/bỏ chọn tất cả hàng"""
        for row in range(self.accounts_table.rowCount()):
            item = self.accounts_table.item(row, 0)
            # Chỉ chọn những hàng có checkbox được kích hoạt (có tài khoản thay thế)
            if item and item.flags() & Qt.ItemIsEnabled:
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
    
    def get_selected_accounts(self):
        """Lấy danh sách các tài khoản đã chọn để thay thế"""
        selected = []
        
        for row in range(self.accounts_table.rowCount()):
            checkbox_item = self.accounts_table.item(row, 0)
            
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                account = self.mismatched_accounts[row]
                login_id = account["login_id"]
                
                # Xác định tài khoản thay thế (có thể là từ ComboBox hoặc từ danh sách)
                replacement = None
                
                if login_id in self.replacement_combos:
                    # Lấy tài khoản từ ComboBox
                    combo = self.replacement_combos[login_id]
                    selected_index = combo.currentIndex()
                    replacement = combo.itemData(selected_index)
                elif login_id in self.replacement_map and self.replacement_map[login_id]:
                    # Lấy tài khoản đầu tiên từ danh sách
                    replacement = self.replacement_map[login_id][0]
                
                if replacement:
                    selected.append({
                        "old_account": account,
                        "new_account": replacement,
                        "action": "login"
                    })
        
        return selected
    
    def accept(self):
        """Xử lý khi người dùng nhấn nút đăng nhập tài khoản đã chọn"""
        # Lưu danh sách các tài khoản đã chọn (được dùng bởi hàm process_mismatched_accounts)
        self.selected_accounts = self.get_selected_accounts()
        
        # Bỏ chọn tất cả các tài khoản đã chọn
        for row in range(self.accounts_table.rowCount()):
            checkbox_item = self.accounts_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                checkbox_item.setCheckState(Qt.Unchecked)
        
        # Gọi phương thức accept của lớp cha để đóng dialog
        super().accept()

# --- Dialog hiển thị tài khoản hết tiền ---
class LowEquityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tài khoản hết tiền (EndEquity < 100)")
        self.resize(1700, 650)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.suggestion_selected = []
        self.accounts = []
        # Nút đăng nhập
        self.login_suggestion_btn = QPushButton("Đăng nhập tài khoản gợi ý đã chọn")
        self.login_suggestion_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 12px; padding: 8px;")
        self.login_suggestion_btn.clicked.connect(self.login_selected_suggestions)
        layout.addWidget(self.login_suggestion_btn)
        # BỎ nút quay lại trang chủ
        # self.back_btn = QPushButton("Quay lại trang chủ")
        # self.back_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; font-size: 12px; padding: 8px;")
        # self.back_btn.clicked.connect(self.close)
        # layout.addWidget(self.back_btn)

    def set_accounts(self, accounts):
        self.accounts = accounts
        self.suggestion_selected = [None] * len(accounts)
        self.table.setRowCount(len(accounts))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Sàn/Broker", "Server", "Login ID", "Chọn sàn gợi ý", "Tài khoản gợi ý đã chọn", "Ghi chú"
        ])
        for row, acc in enumerate(accounts):
            self.table.setItem(row, 0, QTableWidgetItem(acc["broker"]))
            self.table.setItem(row, 1, QTableWidgetItem(acc["server"]))
            self.table.setItem(row, 2, QTableWidgetItem(acc["login_id"]))
            btn = QPushButton("Chọn sàn gợi ý")
            btn.clicked.connect(lambda _, r=row: self.show_suggestion_dialog(r))
            self.table.setCellWidget(row, 3, btn)
            self.table.setItem(row, 4, QTableWidgetItem(""))
            # Thêm ghi chú phân biệt
            note = acc.get("reason", "")
            if note == "Hết tiền":
                note_text = "Tài khoản hết tiền (Equity < 100)"
            elif note == "Không tồn tại trong sheet":
                note_text = "Tài khoản không có trong sheet"
            else:
                note_text = note
            self.table.setItem(row, 5, QTableWidgetItem(note_text))

    def show_suggestion_dialog(self, row):
        acc = self.accounts[row]
        parent = self.parent()
        broker = acc["broker"]
        server = acc["server"]
        login_col_index = parent.get_column_index(parent.login_col_input.text())
        broker_col_index = parent.get_column_index(parent.broker_col_input.text())
        server_col_index = parent.get_column_index(parent.server_col_input.text())
        name_col_index = 2
        equity_col_index = 15  # Cột P - EndEquity
        pass_col_index = parent.get_column_index(parent.pass_col_input.text())
        header_row = 0
        try:
            header_row = int(parent.header_row_input.text()) - 1
            if header_row < 0:
                header_row = 0
        except ValueError:
            header_row = 0
        suggestions = []
        # Chuẩn hóa broker và server để so sánh
        broker_normalized = broker.lower().strip()
        # Tách tên server base
        try:
            if "-" in server:
                server_parts = server.split('-')
                base_server = server_parts[0].strip()
            else:
                base_server = server.strip()
            server_normalized = base_server.lower()
        except Exception as e:
            base_server = server.strip()
            server_normalized = base_server.lower()
        # Tìm tài khoản phù hợp để thay thế
        for row_data in parent.all_data[header_row + 1:]:
            if len(row_data) <= max(login_col_index, broker_col_index, server_col_index, name_col_index, equity_col_index, pass_col_index):
                continue
            sug_login_id = str(row_data[login_col_index]).strip()
            if sug_login_id == acc["login_id"]:
                continue
            sug_broker = str(row_data[broker_col_index]).strip().lower()
            sug_server = str(row_data[server_col_index]).strip().lower()
            # Tách tên server base của tài khoản gợi ý
            try:
                if "-" in sug_server:
                    sug_server_parts = sug_server.split('-')
                    sug_base_server = sug_server_parts[0].strip()
                else:
                    sug_base_server = sug_server.strip()
                sug_server_normalized = sug_base_server.lower()
            except Exception as e:
                sug_base_server = sug_server.strip()
                sug_server_normalized = sug_base_server.lower()
            try:
                equity_str = str(row_data[equity_col_index]).strip()
                equity_value = 0
                if equity_str:
                    if equity_str.count('.') > 1:
                        last_dot = equity_str.rfind('.')
                        equity_str = equity_str.replace('.', '')
                        equity_str = equity_str[:last_dot] + '.' + equity_str[last_dot:]
                    else:
                        equity_str = equity_str.replace(',', '.')
                    equity_value = float(equity_str)
            except Exception as e:
                equity_value = 0
            if equity_value <= 100:
                continue
            name = str(row_data[name_col_index]).strip() if name_col_index < len(row_data) else ""
            password = str(row_data[pass_col_index]).strip() if pass_col_index < len(row_data) else ""
            branch_col_index = parent.get_column_index(parent.branch_col_input.text())
            branch = str(row_data[branch_col_index]).strip() if branch_col_index < len(row_data) else ""
            # Ưu tiên khớp server base
            server_match = (server_normalized and sug_server_normalized and (server_normalized in sug_server_normalized or sug_server_normalized in server_normalized))
            broker_match = (broker_normalized in sug_broker or sug_broker in broker_normalized)
            suggestions.append({
                "login_id": sug_login_id,
                "broker": str(row_data[broker_col_index]).strip(),
                "server": str(row_data[server_col_index]).strip(),
                "name": name,
                "equity": equity_value,
                "password": password,
                "branch": branch,
                "server_match": server_match,
                "broker_match": broker_match
            })
        # Ưu tiên khớp server base
        server_suggestions = [s for s in suggestions if s["server_match"]]
        if not server_suggestions:
            # Nếu không có, ưu tiên khớp broker
            broker_suggestions = [s for s in suggestions if s["broker_match"]]
            filtered = broker_suggestions
        else:
            filtered = server_suggestions
        filtered.sort(key=lambda x: x["equity"], reverse=True)
        if not filtered:
            QMessageBox.information(self, "Không có gợi ý", "Không tìm thấy tài khoản gợi ý phù hợp (ưu tiên cùng server hoặc cùng broker) có EndEquity > 100.")
            return
        items = [f"[{sug['branch']}] ID: {sug['login_id']} | Server: {sug['server']} | Equity: {sug['equity']} | Sàn: {sug['broker']}" for sug in filtered]
        item, ok = QInputDialog.getItem(self, "Chọn tài khoản gợi ý", f"Chọn tài khoản để đăng nhập thay thế cho {acc['login_id']} ({acc.get('reason','')}) :", items, 0, False)
        if ok and item:
            idx = items.index(item)
            self.suggestion_selected[row] = filtered[idx]
            # Cập nhật lại cột 'Tài khoản gợi ý đã chọn' trên bảng
            self.table.setItem(row, 4, QTableWidgetItem(items[idx]))

    def login_selected_suggestions(self):
        parent = self.parent()
        for row, acc in enumerate(self.accounts):
            suggestion = self.suggestion_selected[row] if self.suggestion_selected[row] else None
            if suggestion:
                parent.login_suggestion_to_window(acc, suggestion)
        QMessageBox.information(self, "Kết quả", "Đã gửi lệnh đăng nhập cho các tài khoản gợi ý đã chọn!")

def main():
    # Khởi động ứng dụng với STA (Single-threaded apartment) mode
    # Điều này giúp tương thích với COM trên Windows
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    window = GoogleSheetMT4Login()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 

