"""
Account Manager for JARVIS

Manages MT4/MT5 account data
"""

from typing import List, Dict, Optional
import json
import os


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
    - Load/save accounts
    - Add/remove accounts
    - Search accounts
    """

    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize Account Manager

        Args:
            data_file: Path to accounts data file (JSON)
        """
        self.data_file = data_file or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "config",
            "accounts.json"
        )
        self.accounts: List[Account] = []
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
