import sqlite3
from .profile import Profile
from .account import Account
from .budget_group import BudgetGroup
from .budget_item import BudgetItem
from .budget_item_period import BudgetItemPeriod
from .extrapolation_item import ExtrapolationItem
from .ledger_entry import LedgerEntry


class Database:
    db = sqlite3.connect("budgie.db")

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
        self, profileId, date, amount, income_date, budget_item_id
    ):
        extrapolation_item = ExtrapolationItem(
            date, amount, income_date, budget_item_id
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
