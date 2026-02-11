import sqlite3
import os
from .profile import Profile
from .account import Account
from .budget_group import BudgetGroup
from .budget_item import BudgetItem
from .budget_item_period import BudgetItemPeriod
from .extrapolation_item import ExtrapolationItem
from .ledger_entry import LedgerEntry


class Database:
    # Use environment variable for database path, default to budgie.db
    DB_PATH = os.getenv('DATABASE_PATH', 'budgie.db')
    db = sqlite3.connect(DB_PATH)

    def __init__(self):
        self.create_tables()
        # c = self.db.cursor()
        # c.execute('delete from budget_item where id = 19;')
        # self.db.commit()

    def create_tables(self):
        Profile.create_table(self.db)
        Account.create_table(self.db)
        BudgetGroup.create_table(self.db)
        BudgetItem.create_table(self.db)
        BudgetItemPeriod.create_table(self.db)
        ExtrapolationItem.create_table(self.db)
        LedgerEntry.create_table(self.db)
        self._create_settings_table()
    
    def _create_settings_table(self):
        """Create app settings table for storing app-level preferences."""
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.db.commit()

    def fetch_profiles(self) -> list[Profile]:
        return Profile.fetch_all(self.db)

    def fetch_accounts(self, profileId) -> list[Account]:
        return Account.fetch_all(self.db, profileId)

    def fetch_budget_groups(self, profileId) -> list[BudgetGroup]:
        return BudgetGroup.fetch_all(self.db, profileId)

    def fetch_budget_items(self, profileId) -> list[BudgetItem]:
        return BudgetItem.fetch_all(self.db, profileId)

    def fetch_budget_item_periods(self, itemId) -> list[BudgetItemPeriod]:
        return BudgetItemPeriod.fetch_by_budget_item(self.db, itemId)

    def create_profile(self, name) -> Profile:
        profile = Profile(name)
        profile.create(self.db)
        return profile
    
    def update_profile_hidden_through(self, profile_id: int, hidden_through: str):
        """Update the hidden_through date for a profile."""
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE profiles SET hidden_through = ? WHERE id = ?",
            (hidden_through, profile_id)
        )
        self.db.commit()
    
    def update_profile_theme(self, profile_id: int, theme: str):
        """Update the theme preference for a profile."""
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE profiles SET theme = ? WHERE id = ?",
            (theme, profile_id)
        )
        self.db.commit()
    
    def set_last_profile_id(self, profile_id: int):
        """Store the last selected profile ID."""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO app_settings (key, value)
            VALUES ('last_profile_id', ?)
        """, (str(profile_id),))
        self.db.commit()
    
    def get_last_profile_id(self) -> int | None:
        """Retrieve the last selected profile ID."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT value FROM app_settings WHERE key = 'last_profile_id'
        """)
        row = cursor.fetchone()
        return int(row[0]) if row else None
    
    def get_profile_by_id(self, profile_id: int) -> Profile | None:
        """Fetch a profile by ID."""
        cursor = self.db.cursor()
        cursor.execute("SELECT id, name, hidden_through, theme, created_at FROM profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()
        if row:
            return Profile.from_row(row)
        return None

    def create_account(self, profileId, name, account_type, balance) -> Account:
        account = Account(name, account_type)
        account.balance = balance
        account.create(self.db, profileId)
        return account

    def create_budget_group(self, profileId, name) -> BudgetGroup:
        budget_group = BudgetGroup(name)
        budget_group.create(self.db, profileId)
        return budget_group

    def create_budget_item(
        self, profileId, name, type, amount, group, start_date, end_date, periods
    ):
        budget_item = BudgetItem(
            name, type, amount, start_date, end_date, group, periods
        )
        budget_item.create(self.db, profileId)
        return budget_item

    def create_extrapolation_item(
        self, profileId, date, amount, income_date, budget_item_id, category=None
    ):
        extrapolation_item = ExtrapolationItem(
            date, amount, income_date, budget_item_id, category=category
        )
        extrapolation_item.create(self.db, profileId)
        return extrapolation_item

    def clear_extrapolation_items(self, profileId):
        ExtrapolationItem.clear(self.db, profileId)

    def fetch_extrapolation_items(self, profileId):
        return ExtrapolationItem.fetch_all(self.db, profileId)

    def create_ledger_entry(
        self, name, date, incomeDate, type, amount, accountId
    ) -> LedgerEntry:
        ledger_entry = LedgerEntry(name, date, incomeDate, type, amount, accountId)
        ledger_entry.create(self.db)
        return ledger_entry

    def update_extrapolation_item_ledger_id(
        self, extrapolation_item_id, ledger_entry_id
    ):
        ExtrapolationItem.update_ledger_entry_id(
            self.db, extrapolation_item_id, ledger_entry_id
        )

    def fetch_ledger_items(self, accountId) -> list[LedgerEntry]:
        return LedgerEntry.fetch_by_account(self.db, accountId)

    # Account methods
    def update_account(self, account_id, name, account_type, balance):
        cursor = self.db.cursor()
        from datetime import datetime
        datetime_now = datetime.now()
        cursor.execute(
            """
            UPDATE account
            SET name = ?, type = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, account_type, datetime_now, account_id),
        )
        self.db.commit()
        
        # Return updated account
        cursor.execute(
            "SELECT name, type, id, created_at, updated_at FROM account WHERE id = ?",
            (account_id,),
        )
        row = cursor.fetchone()
        if row:
            account = Account(
                row[0], row[1], row[2],
                datetime.fromisoformat(row[3]),
                datetime.fromisoformat(row[4])
            )
            account.balance = balance
            return account
        return None

    def update_account_balance(self, account_id, amount_delta):
        # Note: Balance is tracked via ledger entries, not in account table
        # This is a placeholder - actual balance should be calculated from ledger
        pass

    # Budget item methods
    def update_budget_item(self, budget_item_id, name, type, amount, group, start_date, end_date, periods):
        from datetime import datetime
        cursor = self.db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            """
            UPDATE budget_item
            SET name = ?, type = ?, amount = ?, budget_group_id = ?,
                start_date = ?, end_date = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, type, amount, group, start_date, end_date, datetime_now, budget_item_id),
        )
        self.db.commit()
        
        # Delete old periods and create new ones
        cursor.execute("DELETE FROM budget_item_period WHERE budget_item_id = ?", (budget_item_id,))
        self.db.commit()
        
        created_periods = []
        for period in periods:
            p = BudgetItemPeriod(period.type, period.value, period.business_day, budget_item_id)
            p.create(self.db)
            created_periods.append(p)
        
        # Return updated item
        from datetime import date
        cursor.execute(
            "SELECT name, type, amount, start_date, end_date, budget_group_id, id, created_at, updated_at FROM budget_item WHERE id = ?",
            (budget_item_id,),
        )
        row = cursor.fetchone()
        if row:
            return BudgetItem(
                row[0], row[1], row[2],
                date.fromisoformat(row[3]),
                date.fromisoformat(row[4]),
                row[5], created_periods, row[6],
                datetime.fromisoformat(row[7]),
                datetime.fromisoformat(row[8])
            )
        return None

    def delete_budget_item(self, budget_item_id):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM budget_item WHERE id = ?", (budget_item_id,))
        self.db.commit()

    # Budget group methods
    def delete_budget_group(self, group_id):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM budget_group WHERE id = ?", (group_id,))
        self.db.commit()

    # Ledger methods
    def get_ledger_entry(self, ledger_item_id):
        from datetime import datetime
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT name, paid_date, income_date, type, amount, account_id, id, created_at, updated_at FROM ledger_entry WHERE id = ?",
            (ledger_item_id,),
        )
        row = cursor.fetchone()
        if row:
            return LedgerEntry(
                row[0],
                datetime.fromisoformat(row[1]),
                datetime.fromisoformat(row[2]),
                row[3], row[4], row[5], row[6],
                datetime.fromisoformat(row[7]),
                datetime.fromisoformat(row[8])
            )
        return None

    def update_ledger_entry(self, ledger_item_id, name, date, income_date, amount, account_id):
        from datetime import datetime
        cursor = self.db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            """
            UPDATE ledger_entry
            SET name = ?, paid_date = ?, income_date = ?, amount = ?,
                account_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, date, income_date, amount, account_id, datetime_now, ledger_item_id),
        )
        self.db.commit()
        return self.get_ledger_entry(ledger_item_id)

    def delete_ledger_entry(self, ledger_item_id):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM ledger_entry WHERE id = ?", (ledger_item_id,))
        self.db.commit()

    # Extrapolation methods
    def get_extrapolation_item(self, item_id):
        from datetime import datetime, date
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT due_date, amount, income_date, budget_item_id, overridden_at, ledger_entry_id, id, created_at, updated_at FROM extrapolation_item WHERE id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if row:
            return ExtrapolationItem(
                date.fromisoformat(row[0]),
                row[1],
                date.fromisoformat(row[2]) if row[2] else None,
                row[3], row[4], row[5], row[6],
                datetime.fromisoformat(row[7]),
                datetime.fromisoformat(row[8])
            )
        return None

    def update_extrapolation_item(self, item_id, amount=None, date=None):
        from datetime import datetime
        cursor = self.db.cursor()
        datetime_now = datetime.now()
        
        if amount is not None and date is not None:
            cursor.execute(
                "UPDATE extrapolation_item SET amount = ?, due_date = ?, updated_at = ? WHERE id = ?",
                (amount, date, datetime_now, item_id),
            )
        elif amount is not None:
            cursor.execute(
                "UPDATE extrapolation_item SET amount = ?, updated_at = ? WHERE id = ?",
                (amount, datetime_now, item_id),
            )
        elif date is not None:
            cursor.execute(
                "UPDATE extrapolation_item SET due_date = ?, updated_at = ? WHERE id = ?",
                (date, datetime_now, item_id),
            )
        
        self.db.commit()
        return self.get_extrapolation_item(item_id)

    def update_extrapolation_item_income_date(self, item_id, income_date):
        from datetime import datetime
        cursor = self.db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            "UPDATE extrapolation_item SET income_date = ?, updated_at = ? WHERE id = ?",
            (income_date, datetime_now, item_id),
        )
        self.db.commit()
