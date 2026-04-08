"""Unit tests for the database model layer and Database CRUD operations."""

import pytest
import sqlite3
from datetime import date, datetime

from database.database import Database
from database.profile import Profile
from database.account import Account
from database.budget_group import BudgetGroup
from database.budget_item import BudgetItem
from database.budget_item_period import BudgetItemPeriod
from database.extrapolation_item import ExtrapolationItem
from database.ledger_entry import LedgerEntry
from database.debt import Debt


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test.db"))


@pytest.fixture
def profile(db):
    return db.create_profile("Test Profile")


@pytest.fixture
def account(db, profile):
    return db.create_account(profile.id, "Checking", "checking", 1000.0)


@pytest.fixture
def budget_group(db, profile):
    return db.create_budget_group(profile.id, "Bills")


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------


class TestDatabaseInit:
    def test_creates_all_tables(self, tmp_path):
        db_path = str(tmp_path / "init.db")
        database = Database(db_path)
        conn = database.db
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        expected = {
            "profiles",
            "account",
            "budget_group",
            "budget_item",
            "budget_item_period",
            "extrapolation_item",
            "ledger_entry",
            "debt",
            "app_settings",
        }
        assert expected.issubset(tables)

    def test_idempotent_on_existing_db(self, tmp_path):
        db_path = str(tmp_path / "idem.db")
        Database(db_path)
        # opening again should not raise
        db2 = Database(db_path)
        assert db2 is not None

    def test_migration_category_column_on_extrapolation_item(self, tmp_path):
        db_path = str(tmp_path / "migrate.db")
        database = Database(db_path)
        cursor = database.db.cursor()
        cursor.execute("PRAGMA table_info(extrapolation_item)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "category" in columns

    def test_migration_debt_id_column_on_budget_item(self, tmp_path):
        db_path = str(tmp_path / "migrate2.db")
        database = Database(db_path)
        cursor = database.db.cursor()
        cursor.execute("PRAGMA table_info(budget_item)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "debt_id" in columns


# ---------------------------------------------------------------------------
# Profile CRUD
# ---------------------------------------------------------------------------


class TestProfileCRUD:
    def test_create_profile_returns_profile_with_id(self, db):
        profile = db.create_profile("My Profile")
        assert isinstance(profile, Profile)
        assert profile.id is not None
        assert profile.name == "My Profile"
        assert profile.created_at is not None

    def test_fetch_profiles_returns_all(self, db):
        db.create_profile("A")
        db.create_profile("B")
        profiles = db.fetch_profiles()
        names = {p.name for p in profiles}
        assert names == {"A", "B"}

    def test_get_profile_by_id_returns_correct(self, db):
        created = db.create_profile("Target")
        fetched = db.get_profile_by_id(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Target"

    def test_get_profile_by_id_returns_none_for_nonexistent(self, db):
        assert db.get_profile_by_id(9999) is None

    def test_delete_profile_cascades(self, db):
        profile = db.create_profile("ToDelete")
        pid = profile.id

        # Create related data
        account = db.create_account(pid, "Acct", "checking", 0)
        group = db.create_budget_group(pid, "Grp")
        period = BudgetItemPeriod("monthly", "1", "false", None)
        db.create_budget_item(
            pid, "Item", "expense", 50, group.id,
            date(2026, 1, 1), date(2026, 12, 31), [period]
        )
        db.create_extrapolation_item(
            pid, date(2026, 2, 1), 50, date(2026, 1, 15), None
        )
        db.create_debt(pid, "Loan", 10000, 5000, 200, 0.05)
        db.create_ledger_entry(
            "Rent", datetime(2026, 3, 1), datetime(2026, 3, 1),
            "expense", 500, account.id
        )

        db.delete_profile(pid)

        assert db.get_profile_by_id(pid) is None
        assert db.fetch_accounts(pid) == []
        assert db.fetch_budget_groups(pid) == []
        assert db.fetch_budget_items(pid) == []
        assert db.fetch_extrapolation_items(pid) == []
        assert db.fetch_debts(pid) == []

    def test_update_profile_hidden_through(self, db):
        profile = db.create_profile("HT")
        db.update_profile_hidden_through(profile.id, "2026-06-01")
        fetched = db.get_profile_by_id(profile.id)
        assert str(fetched.hidden_through) == "2026-06-01"

    def test_update_profile_theme(self, db):
        profile = db.create_profile("Theme")
        db.update_profile_theme(profile.id, "light")
        fetched = db.get_profile_by_id(profile.id)
        assert fetched.theme == "light"


# ---------------------------------------------------------------------------
# Account CRUD
# ---------------------------------------------------------------------------


class TestAccountCRUD:
    def test_create_account_returns_account_with_id(self, db, profile):
        account = db.create_account(profile.id, "Savings", "savings", 500)
        assert isinstance(account, Account)
        assert account.id is not None
        assert account.name == "Savings"
        assert account.account_type == "savings"

    def test_fetch_accounts_scoped_to_profile(self, db):
        p1 = db.create_profile("P1")
        p2 = db.create_profile("P2")
        db.create_account(p1.id, "A1", "checking", 0)
        db.create_account(p2.id, "A2", "savings", 0)

        accts1 = db.fetch_accounts(p1.id)
        accts2 = db.fetch_accounts(p2.id)
        assert len(accts1) == 1
        assert accts1[0].name == "A1"
        assert len(accts2) == 1
        assert accts2[0].name == "A2"

    def test_create_account_creates_starting_balance_ledger(self, db, profile):
        account = db.create_account(profile.id, "New", "checking", 750)
        entries = db.fetch_ledger_items(account.id)
        assert len(entries) == 1
        assert entries[0].name == "Starting Balance"
        assert entries[0].amount == 750

    def test_delete_account_removes_ledger_entries(self, db, profile):
        account = db.create_account(profile.id, "Del", "checking", 100)
        db.create_ledger_entry(
            "Payment", datetime(2026, 3, 1), datetime(2026, 3, 1),
            "expense", 25, account.id
        )
        aid = account.id
        db.delete_account(aid)
        assert db.fetch_ledger_items(aid) == []

    def test_delete_account_clears_extrap_references(self, db, profile):
        account = db.create_account(profile.id, "Del2", "checking", 0)
        ledger = db.create_ledger_entry(
            "Pay", datetime(2026, 3, 1), datetime(2026, 3, 1),
            "expense", 50, account.id
        )
        extrap = db.create_extrapolation_item(
            profile.id, date(2026, 3, 1), 50, date(2026, 3, 1), None
        )
        db.update_extrapolation_item_ledger_id(extrap.id, ledger.id)

        db.delete_account(account.id)

        refreshed = db.get_extrapolation_item(extrap.id)
        assert refreshed.ledger_entry_id is None


# ---------------------------------------------------------------------------
# Budget Item CRUD
# ---------------------------------------------------------------------------


class TestBudgetItemCRUD:
    def _make_periods(self):
        return [BudgetItemPeriod("monthly", "15", "false", None)]

    def test_create_budget_item_returns_item_with_periods(self, db, profile, budget_group):
        periods = self._make_periods()
        item = db.create_budget_item(
            profile.id, "Rent", "expense", 1200,
            budget_group.id, date(2026, 1, 1), date(2026, 12, 31), periods
        )
        assert isinstance(item, BudgetItem)
        assert item.id is not None
        assert item.name == "Rent"
        assert len(item.periods) == 1
        assert item.periods[0].id is not None

    def test_create_budget_item_with_debt_id(self, db, profile, budget_group):
        debt = db.create_debt(profile.id, "Car Loan", 20000, 15000, 400, 0.04)
        periods = self._make_periods()
        item = db.create_budget_item(
            profile.id, "Car Payment", "expense", 400,
            budget_group.id, date(2026, 1, 1), date(2026, 12, 31),
            periods, debt_id=debt.id
        )
        assert item.debt_id == debt.id

    def test_fetch_budget_items_returns_items_with_periods(self, db, profile, budget_group):
        periods = self._make_periods()
        db.create_budget_item(
            profile.id, "Electric", "expense", 100,
            budget_group.id, date(2026, 1, 1), date(2026, 12, 31), periods
        )
        items = db.fetch_budget_items(profile.id)
        assert len(items) == 1
        assert items[0].name == "Electric"
        assert len(items[0].periods) == 1

    def test_update_budget_item(self, db, profile, budget_group):
        periods = self._make_periods()
        item = db.create_budget_item(
            profile.id, "Water", "expense", 60,
            budget_group.id, date(2026, 1, 1), date(2026, 12, 31), periods
        )
        new_periods = [BudgetItemPeriod("weekly", "1", "false", item.id)]
        updated = db.update_budget_item(
            item.id, "Water Bill", "expense", 75,
            budget_group.id, date(2026, 2, 1), date(2026, 12, 31), new_periods
        )
        assert updated.name == "Water Bill"
        assert updated.amount == 75
        assert len(updated.periods) == 1
        assert updated.periods[0].type == "weekly"

    def test_delete_budget_item(self, db, profile, budget_group):
        periods = self._make_periods()
        item = db.create_budget_item(
            profile.id, "Trash", "expense", 30,
            budget_group.id, date(2026, 1, 1), date(2026, 12, 31), periods
        )
        db.delete_budget_item(item.id)
        items = db.fetch_budget_items(profile.id)
        assert len(items) == 0


# ---------------------------------------------------------------------------
# Extrapolation Item CRUD
# ---------------------------------------------------------------------------


class TestExtrapolationItemCRUD:
    def test_create_returns_item_with_id(self, db, profile):
        item = db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 200.0,
            date(2026, 3, 15), None
        )
        assert isinstance(item, ExtrapolationItem)
        assert item.id is not None
        assert item.amount == 200.0

    def test_create_with_category(self, db, profile):
        item = db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 500,
            date(2026, 3, 15), None, category="savings"
        )
        fetched = db.get_extrapolation_item(item.id)
        assert fetched.category == "savings"

    def test_fetch_extrapolation_items(self, db, profile):
        db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 100,
            date(2026, 3, 15), None
        )
        db.create_extrapolation_item(
            profile.id, date(2026, 4, 15), 200,
            date(2026, 3, 15), None
        )
        items = db.fetch_extrapolation_items(profile.id)
        assert len(items) == 2

    def test_clear_extrapolation_items(self, db, profile):
        db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 100,
            date(2026, 3, 15), None
        )
        db.clear_extrapolation_items(profile.id)
        assert db.fetch_extrapolation_items(profile.id) == []

    def test_clear_unpaid_keeps_paid_items(self, db, profile):
        account = db.create_account(profile.id, "Acct", "checking", 0)
        ledger = db.create_ledger_entry(
            "Paid", datetime(2026, 3, 1), datetime(2026, 3, 1),
            "expense", 100, account.id
        )
        paid = db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 100,
            date(2026, 3, 15), None
        )
        db.update_extrapolation_item_ledger_id(paid.id, ledger.id)

        unpaid = db.create_extrapolation_item(
            profile.id, date(2026, 4, 15), 200,
            date(2026, 3, 15), None
        )

        db.clear_unpaid_extrapolation_items(profile.id)
        items = db.fetch_extrapolation_items(profile.id)
        assert len(items) == 1
        assert items[0].id == paid.id

    def test_update_extrapolation_item_amount(self, db, profile):
        item = db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 100,
            date(2026, 3, 15), None
        )
        updated = db.update_extrapolation_item(item.id, amount=150)
        assert updated.amount == 150

    def test_update_extrapolation_item_date(self, db, profile):
        item = db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 100,
            date(2026, 3, 15), None
        )
        updated = db.update_extrapolation_item(item.id, date="2026-05-01")
        assert str(updated.due_date) == "2026-05-01"

    def test_update_extrapolation_item_amount_and_date(self, db, profile):
        item = db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 100,
            date(2026, 3, 15), None
        )
        updated = db.update_extrapolation_item(item.id, amount=250, date="2026-06-01")
        assert updated.amount == 250
        assert str(updated.due_date) == "2026-06-01"

    def test_move_extrapolation_items(self, db, profile, budget_group):
        period = BudgetItemPeriod("monthly", "1", "false", None)
        bi = db.create_budget_item(
            profile.id, "Rent", "expense", 1000,
            budget_group.id, date(2026, 1, 1), date(2026, 12, 31), [period]
        )
        db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 1000,
            date(2026, 3, 15), bi.id
        )
        db.create_extrapolation_item(
            profile.id, date(2026, 4, 1), 1000,
            date(2026, 3, 15), bi.id
        )
        count = db.move_extrapolation_items(
            profile.id, bi.id, "2026-03-15", "2026-04-15"
        )
        assert count == 2
        items = db.fetch_extrapolation_items(profile.id)
        for item in items:
            assert str(item.income_date) == "2026-04-15"


# ---------------------------------------------------------------------------
# Ledger Entry CRUD
# ---------------------------------------------------------------------------


class TestLedgerEntryCRUD:
    def test_create_returns_entry_with_id(self, db, account):
        entry = db.create_ledger_entry(
            "Groceries", datetime(2026, 3, 10), datetime(2026, 3, 1),
            "expense", 85.50, account.id
        )
        assert isinstance(entry, LedgerEntry)
        assert entry.id is not None
        assert entry.name == "Groceries"
        assert entry.amount == 85.50

    def test_fetch_ledger_items_returns_entries_for_account(self, db, account):
        db.create_ledger_entry(
            "Coffee", datetime(2026, 3, 10), datetime(2026, 3, 1),
            "expense", 5, account.id
        )
        entries = db.fetch_ledger_items(account.id)
        # 1 starting balance + 1 new entry
        names = {e.name for e in entries}
        assert "Coffee" in names
        assert "Starting Balance" in names

    def test_update_ledger_entry(self, db, account):
        entry = db.create_ledger_entry(
            "Gas", datetime(2026, 3, 10), datetime(2026, 3, 1),
            "expense", 40, account.id
        )
        updated = db.update_ledger_entry(
            entry.id, "Gasoline", "2026-03-11", "2026-03-01", 45, account.id
        )
        assert updated.name == "Gasoline"
        assert updated.amount == 45

    def test_delete_ledger_entry(self, db, account):
        entry = db.create_ledger_entry(
            "ToDelete", datetime(2026, 3, 10), datetime(2026, 3, 1),
            "expense", 10, account.id
        )
        db.delete_ledger_entry(entry.id)
        fetched = db.get_ledger_entry(entry.id)
        assert fetched is None


# ---------------------------------------------------------------------------
# Debt CRUD
# ---------------------------------------------------------------------------


class TestDebtCRUD:
    def test_create_returns_debt_with_id(self, db, profile):
        debt = db.create_debt(
            profile.id, "Student Loan", 30000, 25000, 300, 0.045
        )
        assert isinstance(debt, Debt)
        assert debt.id is not None
        assert debt.name == "Student Loan"
        assert debt.total_amount == 30000
        assert debt.remaining_amount == 25000
        assert debt.min_payment == 300
        assert debt.interest_rate == 0.045

    def test_fetch_debts_scoped_to_profile(self, db):
        p1 = db.create_profile("D1")
        p2 = db.create_profile("D2")
        db.create_debt(p1.id, "Loan A", 1000, 500, 50, 0.05)
        db.create_debt(p2.id, "Loan B", 2000, 1500, 100, 0.06)

        debts1 = db.fetch_debts(p1.id)
        debts2 = db.fetch_debts(p2.id)
        assert len(debts1) == 1
        assert debts1[0].name == "Loan A"
        assert len(debts2) == 1
        assert debts2[0].name == "Loan B"

    def test_update_debt(self, db, profile):
        debt = db.create_debt(
            profile.id, "Mortgage", 200000, 180000, 1500, 0.035
        )
        updated = db.update_debt(
            debt.id, "Mortgage Updated", 200000, 175000, 1600, 0.03
        )
        assert updated.name == "Mortgage Updated"
        assert updated.remaining_amount == 175000
        assert updated.min_payment == 1600
        assert updated.interest_rate == 0.03

    def test_delete_debt(self, db, profile):
        debt = db.create_debt(
            profile.id, "ToDelete", 5000, 4000, 100, 0.08
        )
        db.delete_debt(debt.id)
        debts = db.fetch_debts(profile.id)
        assert all(d.id != debt.id for d in debts)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


class TestSettings:
    def test_get_setting_returns_none_for_missing(self, db):
        assert db.get_setting("nonexistent_key") is None

    def test_set_setting_stores_value(self, db):
        db.set_setting("theme", "dark")
        assert db.get_setting("theme") == "dark"

    def test_get_setting_after_set_returns_value(self, db):
        db.set_setting("currency", "USD")
        result = db.get_setting("currency")
        assert result == "USD"

    def test_set_setting_overrides_existing(self, db):
        db.set_setting("locale", "en_US")
        db.set_setting("locale", "fr_FR")
        assert db.get_setting("locale") == "fr_FR"

    def test_set_last_profile_id_and_get(self, db, profile):
        db.set_last_profile_id(profile.id)
        assert db.get_last_profile_id() == profile.id

    def test_get_last_profile_id_returns_none_when_unset(self, db):
        assert db.get_last_profile_id() is None


# ---------------------------------------------------------------------------
# Budget Group CRUD
# ---------------------------------------------------------------------------


class TestBudgetGroupCRUD:
    def test_create_budget_group(self, db, profile):
        group = db.create_budget_group(profile.id, "Utilities")
        assert isinstance(group, BudgetGroup)
        assert group.id is not None
        assert group.name == "Utilities"

    def test_fetch_budget_groups_scoped_to_profile(self, db):
        p1 = db.create_profile("G1")
        p2 = db.create_profile("G2")
        db.create_budget_group(p1.id, "GroupA")
        db.create_budget_group(p2.id, "GroupB")

        groups1 = db.fetch_budget_groups(p1.id)
        groups2 = db.fetch_budget_groups(p2.id)
        assert len(groups1) == 1
        assert groups1[0].name == "GroupA"
        assert len(groups2) == 1
        assert groups2[0].name == "GroupB"

    def test_delete_budget_group(self, db, profile):
        group = db.create_budget_group(profile.id, "ToDelete")
        db.delete_budget_group(group.id)
        groups = db.fetch_budget_groups(profile.id)
        assert all(g.id != group.id for g in groups)
