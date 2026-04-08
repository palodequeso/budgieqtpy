import sqlite3
import os
from .profile import Profile
from .account import Account
from .budget_group import BudgetGroup
from .budget_item import BudgetItem
from .budget_item_period import BudgetItemPeriod
from .extrapolation_item import ExtrapolationItem
from .ledger_entry import LedgerEntry
from .debt import Debt


class Database:
    @staticmethod
    def default_db_path() -> str:
        data_dir = os.path.join(
            os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')),
            'budgie'
        )
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'budgie.db')

    def __init__(self, db_path: str = None):
        path = db_path or os.getenv('DATABASE_PATH') or self.default_db_path()
        self.db = sqlite3.connect(path)
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
        Debt.create_table(self.db)
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

    def _resolve_budget_group_id(self, profile_id, group):
        """Resolve a group name string to its integer ID. Pass-through if already an int or None."""
        if group is None or isinstance(group, int):
            return group
        if isinstance(group, str):
            # Try to parse as int first (already an ID stored as string)
            try:
                return int(group)
            except ValueError:
                pass
            # Look up by name
            groups = BudgetGroup.fetch_all(self.db, profile_id)
            match = next((g for g in groups if g.name == group), None)
            return match.id if match else None
        return group

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
    
    def get_setting(self, key: str) -> str | None:
        """Get a setting value by key."""
        cursor = self.db.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def set_setting(self, key: str, value: str):
        """Set a setting value by key."""
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.db.commit()

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
        self, profileId, name, type, amount, group, start_date, end_date, periods, debt_id=None
    ):
        # Resolve group name to group ID
        group_id = self._resolve_budget_group_id(profileId, group)
        budget_item = BudgetItem(
            name, type, amount, start_date, end_date, group_id, periods, debt_id=debt_id
        )
        budget_item.create(self.db, profileId)
        return budget_item

    def create_extrapolation_item(
        self, profileId, date, amount, income_date, budget_item_id, category=None, name=None
    ):
        extrapolation_item = ExtrapolationItem(
            date, amount, income_date, budget_item_id, category=category, name=name
        )
        extrapolation_item.create(self.db, profileId)
        return extrapolation_item

    def clear_extrapolation_items(self, profileId):
        ExtrapolationItem.clear(self.db, profileId)

    def clear_unpaid_extrapolation_items(self, profileId):
        """Clear only unpaid budget-generated extrapolation items.

        Preserves items that were manually created or computed separately:
        debt payments, savings transfers, and one-off entries.
        """
        cursor = self.db.cursor()
        cursor.execute(
            """DELETE FROM extrapolation_item
               WHERE profile_id = ?
                 AND ledger_entry_id IS NULL
                 AND (category IS NULL OR category = '')""",
            (profileId,)
        )
        self.db.commit()

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
    def update_budget_item(self, budget_item_id, name, type, amount, group, start_date, end_date, periods, debt_id=None):
        from datetime import datetime
        # Resolve group name to group ID — need profile_id from the existing item
        cursor = self.db.cursor()
        cursor.execute("SELECT profile_id FROM budget_item WHERE id = ?", (budget_item_id,))
        row = cursor.fetchone()
        profile_id = row[0] if row else None
        group_id = self._resolve_budget_group_id(profile_id, group) if profile_id else group
        datetime_now = datetime.now()
        cursor.execute(
            """
            UPDATE budget_item
            SET name = ?, type = ?, amount = ?, budget_group_id = ?,
                start_date = ?, end_date = ?, updated_at = ?, debt_id = ?
            WHERE id = ?
            """,
            (name, type, amount, group_id, start_date, end_date, datetime_now, debt_id, budget_item_id),
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
            "SELECT due_date, amount, income_date, budget_item_id, overridden_at, ledger_entry_id, id, created_at, updated_at, category FROM extrapolation_item WHERE id = ?",
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
                datetime.fromisoformat(row[8]),
                category=row[9]
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

    def move_extrapolation_items(self, profile_id, budget_item_id, from_income_date, to_income_date):
        """Move all extrapolation items for a budget item from one income date to another."""
        from datetime import datetime
        cursor = self.db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            """UPDATE extrapolation_item
               SET income_date = ?, updated_at = ?
               WHERE profile_id = ? AND budget_item_id = ? AND income_date = ?""",
            (to_income_date, datetime_now, profile_id, budget_item_id, from_income_date),
        )
        count = cursor.rowcount
        self.db.commit()
        return count

    def split_extrapolation_item(self, item_id, keep_amount, remainder_income_date=None):
        """Split an extrapolation item into two: one keeps keep_amount, a new one gets the remainder."""
        from datetime import datetime
        cursor = self.db.cursor()

        # Fetch the original item
        cursor.execute("SELECT * FROM extrapolation_item WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Extrapolation item {item_id} not found")

        cols = [desc[0] for desc in cursor.description]
        item = dict(zip(cols, row))

        original_amount = float(item["amount"])
        keep = float(keep_amount)

        if keep >= abs(original_amount) or keep <= 0:
            raise ValueError("Keep amount must be between 0 and the original amount")

        # For expenses, amounts are negative
        if original_amount < 0:
            new_keep = -abs(keep)
            new_remainder = original_amount - new_keep  # remainder is the rest of the negative
        else:
            new_keep = abs(keep)
            new_remainder = original_amount - new_keep

        now = datetime.now()

        # Update original item with the keep amount
        cursor.execute(
            "UPDATE extrapolation_item SET amount = ?, updated_at = ? WHERE id = ?",
            (new_keep, now, item_id),
        )

        # Create remainder item (same budget_item_id, optionally different income_date)
        dest_income_date = remainder_income_date or item["income_date"]
        cursor.execute(
            """INSERT INTO extrapolation_item
               (due_date, amount, income_date, created_at, updated_at, budget_item_id, profile_id, category)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item["due_date"],
                new_remainder,
                dest_income_date,
                now,
                now,
                item["budget_item_id"],
                item["profile_id"],
                item["category"],
            ),
        )
        remainder_id = cursor.lastrowid
        self.db.commit()

        return {
            "success": True,
            "original_id": item_id,
            "original_amount": new_keep,
            "remainder_id": remainder_id,
            "remainder_amount": new_remainder,
            "remainder_income_date": dest_income_date,
        }

    def delete_profile(self, profile_id):
        """Delete a profile and cascade to all related data."""
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM debt WHERE profile_id = ?", (profile_id,))
        cursor.execute("DELETE FROM extrapolation_item WHERE profile_id = ?", (profile_id,))
        cursor.execute(
            "DELETE FROM budget_item_period WHERE budget_item_id IN (SELECT id FROM budget_item WHERE profile_id = ?)",
            (profile_id,),
        )
        cursor.execute("DELETE FROM budget_item WHERE profile_id = ?", (profile_id,))
        cursor.execute("DELETE FROM budget_group WHERE profile_id = ?", (profile_id,))
        # Delete ledger entries for each account in this profile
        cursor.execute("SELECT id FROM account WHERE profile_id = ?", (profile_id,))
        account_rows = cursor.fetchall()
        for row in account_rows:
            cursor.execute("DELETE FROM ledger_entry WHERE account_id = ?", (row[0],))
        cursor.execute("DELETE FROM account WHERE profile_id = ?", (profile_id,))
        cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        self.db.commit()

    def delete_account(self, account_id):
        """Delete an account and its ledger entries."""
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE extrapolation_item SET ledger_entry_id = NULL WHERE ledger_entry_id IN (SELECT id FROM ledger_entry WHERE account_id = ?)",
            (account_id,),
        )
        cursor.execute("DELETE FROM ledger_entry WHERE account_id = ?", (account_id,))
        cursor.execute("DELETE FROM account WHERE id = ?", (account_id,))
        self.db.commit()

    # Debt methods
    def fetch_debts(self, profileId) -> list[Debt]:
        return Debt.fetch_all(self.db, profileId)

    def create_debt(self, profileId, name, total_amount, remaining_amount, min_payment, interest_rate) -> Debt:
        debt = Debt(name, total_amount, remaining_amount, min_payment, interest_rate)
        debt.create(self.db, profileId)
        return debt

    def update_debt(self, debt_id, name, total_amount, remaining_amount, min_payment, interest_rate):
        from datetime import datetime
        cursor = self.db.cursor()
        datetime_now = datetime.now()
        cursor.execute(
            """
            UPDATE debt
            SET name = ?, total_amount = ?, remaining_amount = ?, min_payment = ?,
                interest_rate = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, total_amount, remaining_amount, min_payment, interest_rate, datetime_now, debt_id),
        )
        self.db.commit()

        cursor.execute(
            "SELECT name, total_amount, remaining_amount, min_payment, interest_rate, profile_id, id, created_at, updated_at FROM debt WHERE id = ?",
            (debt_id,),
        )
        row = cursor.fetchone()
        if row:
            return Debt(
                row[0], row[1], row[2], row[3], row[4], row[5], row[6],
                datetime.fromisoformat(row[7]),
                datetime.fromisoformat(row[8])
            )
        return None

    def delete_debt(self, debt_id):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM debt WHERE id = ?", (debt_id,))
        self.db.commit()
