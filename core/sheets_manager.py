"""
Google Sheets Manager for JARVIS

Quản lý kết nối và lấy dữ liệu tài khoản từ Google Sheets
"""

import os
import json
import pandas as pd
from typing import Optional, List, Dict, Any
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class SheetsManager:
    """
    Quản lý kết nối Google Sheets và lấy dữ liệu tài khoản

    Usage:
        manager = SheetsManager()
        manager.connect(sheet_url, worksheet_name)
        accounts = manager.get_accounts()
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Sheets Manager

        Args:
            credentials_path: Path to credentials.json file
        """
        if credentials_path is None:
            # Tìm credentials.json trong thư mục hiện tại
            credentials_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "credentials.json"
            )

        self.credentials_path = credentials_path
        self.client = None
        self.worksheet = None
        self.df = None
        self.sheet_url = None
        self.worksheet_name = None

    def connect(
        self,
        sheet_url: str,
        worksheet_name: str = "Sheet1",
        header_row: int = 1
    ) -> bool:
        """
        Kết nối đến Google Sheet

        Args:
            sheet_url: URL của Google Sheet
            worksheet_name: Tên worksheet
            header_row: Dòng chứa header (1-indexed)

        Returns:
            True nếu kết nối thành công
        """
        try:
            # Kiểm tra credentials
            if not os.path.exists(self.credentials_path):
                print(f"❌ Không tìm thấy credentials.json tại {self.credentials_path}")
                return False

            # Kết nối Google Sheets API
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path,
                scope
            )
            self.client = gspread.authorize(credentials)

            # Mở Google Sheet
            sheet = self.client.open_by_url(sheet_url)
            self.worksheet = sheet.worksheet(worksheet_name)

            # Lưu thông tin
            self.sheet_url = sheet_url
            self.worksheet_name = worksheet_name

            print(f"✅ Đã kết nối đến sheet: {worksheet_name}")
            return True

        except Exception as e:
            print(f"❌ Lỗi kết nối Google Sheets: {str(e)}")
            return False

    def load_data(
        self,
        data_range: Optional[str] = None,
        header_row: int = 1
    ) -> bool:
        """
        Tải dữ liệu từ worksheet

        Args:
            data_range: Vùng dữ liệu (ví dụ: "A1:J100"), None = all data
            header_row: Dòng chứa header (1-indexed)

        Returns:
            True nếu load thành công
        """
        try:
            if not self.worksheet:
                print("❌ Chưa kết nối đến worksheet")
                return False

            # Lấy tất cả dữ liệu
            if data_range:
                all_data = self.worksheet.get(data_range)
            else:
                all_data = self.worksheet.get_all_values()

            if not all_data or len(all_data) < header_row:
                print("❌ Không có dữ liệu trong worksheet")
                return False

            # Lấy header
            headers = all_data[header_row - 1]

            # Xử lý trùng lặp header
            unique_headers = []
            header_counts = {}
            for h in headers:
                h_clean = str(h).strip()
                if h_clean in header_counts:
                    header_counts[h_clean] += 1
                    unique_headers.append(f"{h_clean}_{header_counts[h_clean]}")
                else:
                    header_counts[h_clean] = 0
                    unique_headers.append(h_clean)

            # Lấy data rows
            data_rows = all_data[header_row:]

            # Tạo records
            records = []
            for row in data_rows:
                # Bỏ qua dòng trống
                if not any(row):
                    continue

                # Đảm bảo row có đủ số cột
                if len(row) < len(unique_headers):
                    row = row + [''] * (len(unique_headers) - len(row))

                # Cắt nếu row dài hơn
                row = row[:len(unique_headers)]

                record = dict(zip(unique_headers, row))
                records.append(record)

            # Convert to DataFrame
            self.df = pd.DataFrame(records)

            print(f"✅ Đã tải {len(self.df)} tài khoản từ Google Sheets")
            return True

        except Exception as e:
            print(f"❌ Lỗi khi load data: {str(e)}")
            return False

    def get_accounts(
        self,
        filter_dict: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tài khoản

        Args:
            filter_dict: Dictionary để lọc (ví dụ: {"Broker": "Exness"})

        Returns:
            List of account dictionaries
        """
        if self.df is None:
            print("❌ Chưa load dữ liệu")
            return []

        df = self.df.copy()

        # Áp dụng filter nếu có
        if filter_dict:
            for col, value in filter_dict.items():
                if col in df.columns:
                    df = df[df[col].astype(str).str.contains(value, case=False, na=False)]

        # Convert to list of dicts
        return df.to_dict('records')

    def search_accounts(self, query: str) -> List[Dict[str, Any]]:
        """
        Tìm kiếm tài khoản theo query

        Args:
            query: Chuỗi tìm kiếm

        Returns:
            List of matching accounts
        """
        if self.df is None:
            return []

        # Tìm kiếm trong tất cả các cột
        mask = self.df.astype(str).apply(
            lambda row: row.str.contains(query, case=False, na=False).any(),
            axis=1
        )

        filtered_df = self.df[mask]
        return filtered_df.to_dict('records')

    def find_account(
        self,
        login: Optional[str] = None,
        broker: Optional[str] = None,
        platform: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Tìm 1 tài khoản cụ thể

        Args:
            login: Login ID
            broker: Broker name
            platform: MT4 hoặc MT5

        Returns:
            Account dict hoặc None
        """
        if self.df is None:
            return None

        df = self.df.copy()

        # Áp dụng filters
        if login:
            # Tìm cột chứa login (có thể là "Login", "ID", "Account ID", etc.)
            login_cols = [col for col in df.columns if any(
                keyword in col.lower()
                for keyword in ['login', 'id', 'account']
            )]

            if login_cols:
                mask = False
                for col in login_cols:
                    mask |= df[col].astype(str).str.contains(login, case=False, na=False)
                df = df[mask]

        if broker:
            # Tìm cột broker
            broker_cols = [col for col in df.columns if 'broker' in col.lower()]
            if broker_cols:
                mask = False
                for col in broker_cols:
                    mask |= df[col].astype(str).str.contains(broker, case=False, na=False)
                df = df[mask]

        if platform:
            # Tìm cột platform
            platform_cols = [col for col in df.columns if any(
                keyword in col.lower()
                for keyword in ['platform', 'mt4', 'mt5', 'type']
            )]
            if platform_cols:
                mask = False
                for col in platform_cols:
                    mask |= df[col].astype(str).str.contains(platform, case=False, na=False)
                df = df[mask]

        # Trả về account đầu tiên nếu có
        if len(df) > 0:
            return df.iloc[0].to_dict()

        return None

    def get_column_names(self) -> List[str]:
        """Lấy danh sách tên cột"""
        if self.df is None:
            return []
        return list(self.df.columns)

    def get_unique_values(self, column: str) -> List[str]:
        """
        Lấy các giá trị unique trong 1 cột

        Args:
            column: Tên cột

        Returns:
            List of unique values
        """
        if self.df is None or column not in self.df.columns:
            return []

        return self.df[column].dropna().unique().tolist()

    def refresh(self) -> bool:
        """
        Refresh dữ liệu từ Google Sheets

        Returns:
            True nếu refresh thành công
        """
        if not self.sheet_url or not self.worksheet_name:
            print("❌ Chưa kết nối đến sheet")
            return False

        return self.load_data()

    def get_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê về dữ liệu

        Returns:
            Dictionary chứa stats
        """
        if self.df is None:
            return {}

        stats = {
            "total_accounts": len(self.df),
            "columns": list(self.df.columns),
            "data_loaded": True
        }

        # Thống kê theo broker (nếu có cột broker)
        broker_cols = [col for col in self.df.columns if 'broker' in col.lower()]
        if broker_cols:
            stats["by_broker"] = self.df[broker_cols[0]].value_counts().to_dict()

        # Thống kê theo platform (nếu có)
        platform_cols = [col for col in self.df.columns if any(
            keyword in col.lower()
            for keyword in ['platform', 'type']
        )]
        if platform_cols:
            stats["by_platform"] = self.df[platform_cols[0]].value_counts().to_dict()

        return stats


# Helper function để map từ Google Sheets data sang Account format
def sheets_account_to_account_dict(sheets_account: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert account từ Google Sheets format sang Account format chuẩn

    Args:
        sheets_account: Dict từ Google Sheets

    Returns:
        Dict format chuẩn cho Account
    """
    # Tìm các fields tương ứng
    result = {}

    # Login - tìm trong các cột có thể
    for key in sheets_account.keys():
        key_lower = key.lower()

        if 'login' in key_lower or 'id' in key_lower or 'account' in key_lower:
            if not result.get('login'):
                result['login'] = str(sheets_account[key])

        elif 'broker' in key_lower or 'sàn' in key_lower:
            if not result.get('broker'):
                result['broker'] = str(sheets_account[key])

        elif 'server' in key_lower or 'máy chủ' in key_lower:
            if not result.get('server'):
                result['server'] = str(sheets_account[key])

        elif 'pass' in key_lower or 'password' in key_lower or 'mật khẩu' in key_lower:
            if not result.get('password'):
                result['password'] = str(sheets_account[key])

        elif 'platform' in key_lower or 'type' in key_lower or 'loại' in key_lower:
            if not result.get('platform'):
                platform = str(sheets_account[key]).upper()
                if 'MT5' in platform or '5' in platform:
                    result['platform'] = 'MT5'
                elif 'MT4' in platform or '4' in platform:
                    result['platform'] = 'MT4'
                else:
                    result['platform'] = platform

        elif 'name' in key_lower or 'tên' in key_lower:
            if not result.get('name'):
                result['name'] = str(sheets_account[key])

    # Defaults
    if not result.get('platform'):
        result['platform'] = 'MT4'  # Default

    if not result.get('status'):
        result['status'] = 'inactive'

    return result


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("SHEETS MANAGER TEST")
    print("=" * 80)

    manager = SheetsManager()

    # Test connection (cần credentials.json và sheet URL thật)
    # sheet_url = "YOUR_SHEET_URL_HERE"
    # if manager.connect(sheet_url, "Sheet1"):
    #     if manager.load_data():
    #         accounts = manager.get_accounts()
    #         print(f"\nTìm thấy {len(accounts)} tài khoản")
    #
    #         if accounts:
    #             print("\nTài khoản đầu tiên:")
    #             print(accounts[0])

    print("\n⚠️  Để test, cần:")
    print("  1. credentials.json trong thư mục JARVIS")
    print("  2. Google Sheet URL hợp lệ")
    print("  3. Uncomment code test phía trên")
