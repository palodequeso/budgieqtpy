"""
Ledger Service - Handles all ledger-related business logic.
Used by both Qt app and API.
"""

from datetime import date, datetime
from database.database import Database
from database.ledger_entry import LedgerEntry


class LedgerService:
    """Service for ledger operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_ledger_entries(self, account_id: int) -> list[LedgerEntry]:
        """Get all ledger entries for an account."""
        return self.db.fetch_ledger_items(account_id)
    
    def get_ledger_entry_by_id(self, ledger_item_id: int) -> LedgerEntry:
        """Get a specific ledger entry by ID."""
        return self.db.get_ledger_entry(ledger_item_id)
    
    def create_ledger_entry(
        self,
        account_id: int,
        amount: float,
        paid_date: str,
        income_date: str,
        name: str = None,
        entry_type: str = "Expense",
        budget_item_id: int = None
    ) -> LedgerEntry:
        """Create a new ledger entry and update account balance."""
        # Convert string dates to date objects if needed
        if isinstance(paid_date, str):
            paid_date = datetime.fromisoformat(paid_date).date() if 'T' in paid_date else date.fromisoformat(paid_date)
        if isinstance(income_date, str):
            income_date = datetime.fromisoformat(income_date).date() if 'T' in income_date else date.fromisoformat(income_date)
        
        entry = self.db.create_ledger_entry(
            name=name or "Ledger Entry",
            date=paid_date,
            incomeDate=income_date,
            type=entry_type,
            amount=amount,
            accountId=account_id
        )
        
        # Update account balance
        # Note: In current architecture, balance is calculated from ledger
        # This is a placeholder that could adjust account records if needed
        self.db.update_account_balance(account_id, -amount)
        
        return entry
    
    def update_ledger_entry(
        self,
        ledger_item_id: int,
        account_id: int,
        amount: float,
        paid_date: str,
        income_date: str,
        name: str = None
    ) -> LedgerEntry:
        """Update an existing ledger entry."""
        # Convert string dates to date objects if needed
        if isinstance(paid_date, str):
            paid_date = datetime.fromisoformat(paid_date).date() if 'T' in paid_date else date.fromisoformat(paid_date)
        if isinstance(income_date, str):
            income_date = datetime.fromisoformat(income_date).date() if 'T' in income_date else date.fromisoformat(income_date)
        
        # Get old entry to reverse balance change
        old_entry = self.db.get_ledger_entry(ledger_item_id)
        if old_entry:
            self.db.update_account_balance(old_entry.account_id, old_entry.amount)
        
        # Update entry
        updated_entry = self.db.update_ledger_entry(
            ledger_item_id=ledger_item_id,
            name=name or "Ledger Entry",
            date=paid_date,
            income_date=income_date,
            amount=amount,
            account_id=account_id
        )
        
        # Apply new balance change
        self.db.update_account_balance(account_id, -amount)
        
        return updated_entry
    
    def delete_ledger_entry(self, ledger_item_id: int) -> None:
        """Delete a ledger entry and reverse balance change."""
        # Get entry to reverse balance
        entry = self.db.get_ledger_entry(ledger_item_id)
        if entry:
            self.db.update_account_balance(entry.account_id, entry.amount)
        
        self.db.delete_ledger_entry(ledger_item_id)
    
    def mark_extrapolation_item_paid(
        self,
        extrapolation_item_id: int,
        account_id: int,
        paid_date: str = None
    ) -> LedgerEntry:
        """
        Mark an extrapolation item as paid by creating a ledger entry.
        This is used when scheduling items and marking them as paid.
        """
        # Get the extrapolation item
        extrap_item = self.db.get_extrapolation_item(extrapolation_item_id)
        if not extrap_item:
            raise ValueError(f"Extrapolation item {extrapolation_item_id} not found")
        
        # Check if already paid
        if extrap_item.ledger_entry_id is not None:
            raise ValueError(f"Extrapolation item {extrapolation_item_id} is already marked as paid (ledger entry {extrap_item.ledger_entry_id})")
        
        # Create ledger entry
        ledger_entry = self.create_ledger_entry(
            account_id=account_id,
            amount=extrap_item.amount,
            paid_date=paid_date or date.today().isoformat(),
            income_date=extrap_item.income_date.isoformat() if hasattr(extrap_item.income_date, 'isoformat') else str(extrap_item.income_date),
            name=f"Paid item {extrapolation_item_id}",
            entry_type="Expense",
            budget_item_id=extrap_item.budget_item_id
        )
        
        # Link ledger entry to extrapolation item
        self.db.update_extrapolation_item_ledger_id(extrapolation_item_id, ledger_entry.id)
        
        return ledger_entry
