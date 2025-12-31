"""
Account Manager for JARVIS

Manages MT4/MT5 account data
Supports Google Sheets integration
"""

from typing import List, Dict, Optional, Any
import json
import os
from .sheets_manager import SheetsManager, sheets_account_to_account_dict


class Account:
    """Represents a trading account"""

    def __init__(
        self,
        login: str,
        broker: str,
        platform: str,
        server: str,
        password: Optional[str] = None,
        name: Optional[str] = None,
        status: str = "inactive"
    ):
        self.login = login
        self.broker = broker
        self.platform = platform
        self.server = server
        self.password = password  # Optional, can be stored encrypted
        self.name = name or f"{broker} - {login}"
        self.status = status  # active, inactive, error

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "login": self.login,
            "broker": self.broker,
            "platform": self.platform,
            "server": self.server,
            "password": self.password,
            "name": self.name,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Account':
        """Create from dictionary"""
        return cls(**data)


class AccountManager:
    """
    Manages trading accounts

    Features:
    - Load/save accounts from JSON
    - Google Sheets integration
    - Add/remove accounts
    - Search and query accounts
    """

    def __init__(
        self,
        data_file: Optional[str] = None,
        use_sheets: bool = False,
        credentials_path: Optional[str] = None
    ):
        """
        Initialize Account Manager

        Args:
            data_file: Path to accounts data file (JSON)
            use_sheets: Enable Google Sheets integration
            credentials_path: Path to Google credentials.json
        """
        self.data_file = data_file or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "config",
            "accounts.json"
        )
        self.accounts: List[Account] = []
        self.use_sheets = use_sheets
        self.sheets_manager: Optional[SheetsManager] = None

        # Initialize Sheets Manager if enabled
        if use_sheets:
            self.sheets_manager = SheetsManager(credentials_path)

        self.load_accounts()

    def load_accounts(self):
        """Load accounts from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accounts = [
                        Account.from_dict(acc) for acc in data
                    ]
                print(f"✅ Loaded {len(self.accounts)} accounts")
            else:
                print("ℹ️ No accounts file found, starting fresh")
                self.accounts = []
        except Exception as e:
            print(f"⚠️ Error loading accounts: {str(e)}")
            self.accounts = []

    def save_accounts(self):
        """Save accounts to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

            with open(self.data_file, 'w', encoding='utf-8') as f:
                data = [acc.to_dict() for acc in self.accounts]
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved {len(self.accounts)} accounts")
        except Exception as e:
            print(f"⚠️ Error saving accounts: {str(e)}")

    def add_account(self, account: Account) -> bool:
        """
        Add an account

        Args:
            account: Account object

        Returns:
            True if added successfully
        """
        # Check if already exists
        if self.find_account(account.login, account.broker):
            print(f"⚠️ Account already exists: {account.login}")
            return False

        self.accounts.append(account)
        self.save_accounts()
        return True

    def remove_account(self, login: str, broker: str) -> bool:
        """
        Remove an account

        Args:
            login: Login ID
            broker: Broker name

        Returns:
            True if removed successfully
        """
        account = self.find_account(login, broker)
        if account:
            self.accounts.remove(account)
            self.save_accounts()
            return True
        return False

    def find_account(self, login: str, broker: str) -> Optional[Account]:
        """
        Find account by login and broker

        Args:
            login: Login ID
            broker: Broker name

        Returns:
            Account or None
        """
        for acc in self.accounts:
            if acc.login == login and acc.broker.lower() == broker.lower():
                return acc
        return None

    def get_all_accounts(self) -> List[Account]:
        """Get all accounts"""
        return self.accounts

    def get_accounts_by_platform(self, platform: str) -> List[Account]:
        """Get accounts by platform (MT4 or MT5)"""
        return [acc for acc in self.accounts if acc.platform == platform]

    def update_account_status(self, login: str, broker: str, status: str):
        """Update account status"""
        account = self.find_account(login, broker)
        if account:
            account.status = status
            self.save_accounts()

    # ========== GOOGLE SHEETS METHODS ==========

    def connect_sheets(
        self,
        sheet_url: str,
        worksheet_name: str = "Sheet1",
        header_row: int = 1
    ) -> bool:
        """
        Kết nối đến Google Sheets

        Args:
            sheet_url: URL của Google Sheet
            worksheet_name: Tên worksheet
            header_row: Dòng chứa header

        Returns:
            True nếu kết nối thành công
        """
        if not self.sheets_manager:
            self.sheets_manager = SheetsManager()

        return self.sheets_manager.connect(sheet_url, worksheet_name, header_row)

    def load_from_sheets(
        self,
        data_range: Optional[str] = None,
        merge_with_local: bool = True
    ) -> bool:
        """
        Load accounts từ Google Sheets

        Args:
            data_range: Vùng dữ liệu (None = all)
            merge_with_local: Merge với accounts local hay replace

        Returns:
            True nếu load thành công
        """
        if not self.sheets_manager:
            print("❌ Chưa kết nối Google Sheets")
            return False

        # Load data from sheets
        if not self.sheets_manager.load_data(data_range):
            return False

        # Get accounts from sheets
        sheets_accounts = self.sheets_manager.get_accounts()

        # Convert to Account objects
        new_accounts = []
        for sheet_acc in sheets_accounts:
            try:
                # Convert from sheets format to standard format
                acc_dict = sheets_account_to_account_dict(sheet_acc)

                # Create Account object
                account = Account(
                    login=acc_dict.get('login', ''),
                    broker=acc_dict.get('broker', 'Unknown'),
                    platform=acc_dict.get('platform', 'MT4'),
                    server=acc_dict.get('server', ''),
                    password=acc_dict.get('password'),
                    name=acc_dict.get('name'),
                    status=acc_dict.get('status', 'inactive')
                )

                # Validate có login không
                if account.login:
                    new_accounts.append(account)

            except Exception as e:
                print(f"⚠️ Lỗi khi convert account: {str(e)}")
                continue

        # Merge or replace
        if merge_with_local:
            # Merge: add new accounts, update existing
            for new_acc in new_accounts:
                existing = self.find_account(new_acc.login, new_acc.broker)
                if existing:
                    # Update existing
                    existing.server = new_acc.server
                    existing.platform = new_acc.platform
                    existing.password = new_acc.password or existing.password
                    existing.name = new_acc.name or existing.name
                else:
                    # Add new
                    self.accounts.append(new_acc)
        else:
            # Replace all
            self.accounts = new_accounts

        # Save to JSON
        self.save_accounts()

        print(f"✅ Đã load {len(new_accounts)} accounts từ Google Sheets")
        return True

    def refresh_from_sheets(self) -> bool:
        """
        Refresh accounts từ Google Sheets

        Returns:
            True nếu refresh thành công
        """
        if not self.sheets_manager:
            return False

        if self.sheets_manager.refresh():
            return self.load_from_sheets(merge_with_local=True)

        return False

    def search_accounts(
        self,
        query: Optional[str] = None,
        broker: Optional[str] = None,
        platform: Optional[str] = None,
        login: Optional[str] = None
    ) -> List[Account]:
        """
        Search accounts với nhiều filters

        Args:
            query: Text search (tìm trong tất cả fields)
            broker: Filter theo broker
            platform: Filter theo platform (MT4/MT5)
            login: Filter theo login ID

        Returns:
            List of matching accounts
        """
        results = self.accounts.copy()

        # Filter by login
        if login:
            results = [acc for acc in results if login.lower() in acc.login.lower()]

        # Filter by broker
        if broker:
            results = [acc for acc in results if broker.lower() in acc.broker.lower()]

        # Filter by platform
        if platform:
            results = [acc for acc in results if platform.upper() in acc.platform.upper()]

        # Text search
        if query:
            query_lower = query.lower()
            results = [
                acc for acc in results
                if (query_lower in acc.login.lower() or
                    query_lower in acc.broker.lower() or
                    query_lower in acc.server.lower() or
                    (acc.name and query_lower in acc.name.lower()))
            ]

        return results

    def get_account_info(self, login: str, broker: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin chi tiết của 1 account

        Args:
            login: Login ID
            broker: Broker name (optional)

        Returns:
            Dict chứa thông tin account hoặc None
        """
        # Tìm account
        if broker:
            account = self.find_account(login, broker)
        else:
            # Tìm login trong tất cả brokers
            matches = [acc for acc in self.accounts if acc.login == login]
            account = matches[0] if matches else None

        if account:
            return {
                "login": account.login,
                "broker": account.broker,
                "platform": account.platform,
                "server": account.server,
                "name": account.name,
                "status": account.status,
                "has_password": bool(account.password)
            }

        return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê về accounts

        Returns:
            Dict chứa stats
        """
        stats = {
            "total": len(self.accounts),
            "by_platform": {},
            "by_broker": {},
            "by_status": {}
        }

        for acc in self.accounts:
            # By platform
            stats["by_platform"][acc.platform] = stats["by_platform"].get(acc.platform, 0) + 1

            # By broker
            stats["by_broker"][acc.broker] = stats["by_broker"].get(acc.broker, 0) + 1

            # By status
            stats["by_status"][acc.status] = stats["by_status"].get(acc.status, 0) + 1

        return stats


# Test
if __name__ == "__main__":
    print("=" * 80)
    print("ACCOUNT MANAGER TEST")
    print("=" * 80)

    manager = AccountManager()

    # Add test account
    test_account = Account(
        login="12345678",
        broker="Exness",
        platform="MT5",
        server="Exness-MT5Live",
        password="TestPass123"
    )

    manager.add_account(test_account)

    # List accounts
    print(f"\nTotal accounts: {len(manager.get_all_accounts())}")
    for acc in manager.get_all_accounts():
        print(f"  - {acc.name} ({acc.platform})")
