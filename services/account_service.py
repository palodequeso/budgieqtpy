"""
Account Service - Handles all account-related business logic.
Used by both Qt app and API.
"""

from database.database import Database
from database.account import Account


class AccountService:
    """Service for account operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_accounts(self, profile_id: int) -> list[Account]:
        """Get all accounts for a profile."""
        return self.db.fetch_accounts(profile_id)
    
    def get_account_by_id(self, account_id: int, profile_id: int) -> Account:
        """Get a specific account by ID."""
        accounts = self.db.fetch_accounts(profile_id)
        for account in accounts:
            if account.id == account_id:
                return account
        return None
    
    def create_account(self, profile_id: int, name: str, account_type: str, balance: float) -> Account:
        """Create a new account."""
        return self.db.create_account(
            profileId=profile_id,
            name=name,
            account_type=account_type,
            balance=balance
        )
    
    def update_account(self, account_id: int, name: str, account_type: str, balance: float) -> Account:
        """Update an existing account."""
        return self.db.update_account(
            account_id=account_id,
            name=name,
            account_type=account_type,
            balance=balance
        )
    
    def delete_account(self, account_id: int) -> None:
        """Delete an account."""
        # TODO: Implement delete_account in database
        raise NotImplementedError("Account deletion not yet implemented")
    
    def get_account_balance(self, account_id: int) -> float:
        """
        Calculate account balance from ledger entries.
        This is the correct way to get balance (not from account table).
        """
        ledger_entries = self.db.fetch_ledger_items(account_id)
        balance = 0.0
        for entry in ledger_entries:
            balance += entry.amount
        return balance
