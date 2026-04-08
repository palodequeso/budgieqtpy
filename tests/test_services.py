"""
Unit tests for the service layer.

Uses real SQLite databases via tmp_path for isolation.
Only external services (LLM API calls) are mocked.
"""

import pytest
from datetime import date, datetime, timedelta

from database.database import Database
from services.reconciliation_service import ReconciliationService
from services.ledger_service import LedgerService
from services.account_service import AccountService
from services.debt_service import DebtService
from services.ai_service import AIService
from services.calendar_service import CalendarService
from services.profile_service import ProfileService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_db(tmp_path):
    """Create a fresh Database backed by a temporary SQLite file."""
    db = Database(str(tmp_path / "test.db"))
    return db


@pytest.fixture
def profile(test_db):
    """Create a default test profile."""
    return test_db.create_profile("Test Profile")


@pytest.fixture
def account(test_db, profile):
    """Create a default test account (balance 0)."""
    return test_db.create_account(
        profileId=profile.id,
        name="Checking",
        account_type="checking",
        balance=0,
    )


# ===========================================================================
# ReconciliationService
# ===========================================================================

class TestReconciliationParseDate:
    """Tests for ReconciliationService._parse_date."""

    def setup_method(self):
        # _parse_date is stateless; we only need an instance (db unused)
        self.svc = ReconciliationService.__new__(ReconciliationService)

    def test_iso_format(self):
        assert self.svc._parse_date("2025-03-15") == date(2025, 3, 15)

    def test_us_format(self):
        assert self.svc._parse_date("03/15/2025") == date(2025, 3, 15)

    def test_us_short_year(self):
        assert self.svc._parse_date("03/15/25") == date(2025, 3, 15)

    def test_single_digit_month_day(self):
        # M/D/YYYY — strptime with %m/%d/%Y handles zero-padded or single digits
        assert self.svc._parse_date("3/5/2025") == date(2025, 3, 5)

    def test_invalid_returns_none(self):
        assert self.svc._parse_date("not-a-date") is None

    def test_empty_string_returns_none(self):
        assert self.svc._parse_date("") is None

    def test_partial_date_returns_none(self):
        assert self.svc._parse_date("2025-13-01") is None  # month 13


class TestReconciliationParseAmount:
    """Tests for ReconciliationService._parse_amount."""

    def setup_method(self):
        self.svc = ReconciliationService.__new__(ReconciliationService)

    def test_plain_number(self):
        assert self.svc._parse_amount("123.45") == 123.45

    def test_dollar_sign(self):
        assert self.svc._parse_amount("$1,234.56") == 1234.56

    def test_commas_only(self):
        assert self.svc._parse_amount("1,000") == 1000.0

    def test_parentheses_negative(self):
        assert self.svc._parse_amount("(100.00)") == -100.00

    def test_parentheses_with_dollar(self):
        assert self.svc._parse_amount("($50.00)") == -50.00

    def test_negative_sign(self):
        assert self.svc._parse_amount("-75.25") == -75.25

    def test_invalid_returns_none(self):
        assert self.svc._parse_amount("abc") is None

    def test_empty_returns_none(self):
        assert self.svc._parse_amount("") is None


class TestReconciliationDetectColumn:
    """Tests for ReconciliationService._detect_column."""

    def setup_method(self):
        self.svc = ReconciliationService.__new__(ReconciliationService)

    def test_exact_match_case_insensitive(self):
        headers = ["Date", "Amount", "Description"]
        result = self.svc._detect_column(headers, ["date"])
        assert result == "Date"

    def test_exact_match_with_spaces(self):
        headers = ["Transaction Date", "Debit", "Memo"]
        result = self.svc._detect_column(headers, ["transaction date"])
        assert result == "Transaction Date"

    def test_partial_match(self):
        headers = ["Post Date/Time", "Total Amount", "Notes"]
        result = self.svc._detect_column(headers, ["date"])
        assert result == "Post Date/Time"

    def test_fallback_to_first_column(self):
        headers = ["Col A", "Col B", "Col C"]
        result = self.svc._detect_column(headers, ["zzz_no_match"])
        assert result == "Col A"

    def test_empty_headers_returns_none(self):
        result = self.svc._detect_column([], ["date"])
        assert result is None


class TestReconciliationParseCSV:
    """Tests for ReconciliationService.parse_csv."""

    def setup_method(self):
        self.svc = ReconciliationService.__new__(ReconciliationService)

    def test_complete_data(self):
        csv_text = (
            "Date,Amount,Description\n"
            "2025-03-01,$100.00,Grocery Store\n"
            "2025-03-02,$50.00,Gas Station\n"
        )
        result = self.svc.parse_csv(csv_text)
        assert result["count"] == 2
        assert result["detected_columns"]["date"] == "Date"
        assert result["detected_columns"]["amount"] == "Amount"
        assert result["detected_columns"]["description"] == "Description"
        assert result["transactions"][0]["amount"] == 100.00
        assert result["transactions"][0]["date"] == "2025-03-01"
        assert result["transactions"][0]["description"] == "Grocery Store"

    def test_skips_rows_with_missing_date(self):
        csv_text = (
            "Date,Amount,Description\n"
            ",100.00,Good row missing date\n"
            "2025-03-02,50.00,Valid\n"
        )
        result = self.svc.parse_csv(csv_text)
        assert result["count"] == 1
        assert result["transactions"][0]["description"] == "Valid"

    def test_skips_rows_with_missing_amount(self):
        csv_text = (
            "Date,Amount,Description\n"
            "2025-03-01,,Missing amount\n"
            "2025-03-02,50.00,Valid\n"
        )
        result = self.svc.parse_csv(csv_text)
        assert result["count"] == 1

    def test_skips_rows_with_unparseable_date(self):
        csv_text = (
            "Date,Amount,Description\n"
            "not-a-date,100.00,Bad date\n"
            "2025-03-02,50.00,Valid\n"
        )
        result = self.svc.parse_csv(csv_text)
        assert result["count"] == 1

    def test_skips_rows_with_unparseable_amount(self):
        csv_text = (
            "Date,Amount,Description\n"
            "2025-03-01,abc,Bad amount\n"
            "2025-03-02,50.00,Valid\n"
        )
        result = self.svc.parse_csv(csv_text)
        assert result["count"] == 1

    def test_explicit_column_names(self):
        csv_text = (
            "Col1,Col2,Col3\n"
            "2025-03-01,100.00,Purchase\n"
        )
        result = self.svc.parse_csv(csv_text, date_col="Col1", amount_col="Col2", desc_col="Col3")
        assert result["count"] == 1
        assert result["transactions"][0]["description"] == "Purchase"

    def test_empty_csv(self):
        csv_text = "Date,Amount,Description\n"
        result = self.svc.parse_csv(csv_text)
        assert result["count"] == 0
        assert result["transactions"] == []


class TestReconciliationMatchTransactions:
    """Tests for ReconciliationService.match_transactions."""

    def test_exact_match_high_confidence(self, test_db, profile, account):
        svc = ReconciliationService(test_db)
        # Create an unpaid extrapolation item
        test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-100.00,
            income_date="2025-03-01",
            budget_item_id=None,
            category=None,
        )
        transactions = [{"date": "2025-03-15", "amount": 100.00, "description": "Rent"}]
        results = svc.match_transactions(profile.id, transactions, account.id)
        assert len(results) == 1
        assert results[0]["status"] == "matched"
        assert results[0]["match"]["confidence"] == 100

    def test_close_amount_within_tolerance(self, test_db, profile, account):
        svc = ReconciliationService(test_db)
        test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-100.00,
            income_date="2025-03-01",
            budget_item_id=None,
        )
        # 5% off — within default 10% tolerance
        transactions = [{"date": "2025-03-15", "amount": 95.00, "description": "Close"}]
        results = svc.match_transactions(profile.id, transactions, account.id)
        assert results[0]["status"] == "matched"
        assert results[0]["match"]["confidence"] > 0

    def test_amount_too_far_off(self, test_db, profile, account):
        svc = ReconciliationService(test_db)
        test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-100.00,
            income_date="2025-03-01",
            budget_item_id=None,
        )
        # 50% off — way beyond 10% tolerance
        transactions = [{"date": "2025-03-15", "amount": 50.00, "description": "Too far"}]
        results = svc.match_transactions(profile.id, transactions, account.id)
        assert results[0]["status"] == "unmatched"

    def test_date_too_far_off(self, test_db, profile, account):
        svc = ReconciliationService(test_db)
        test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-100.00,
            income_date="2025-03-01",
            budget_item_id=None,
        )
        # 30 days off — beyond default 5-day tolerance
        transactions = [{"date": "2025-04-15", "amount": 100.00, "description": "Late"}]
        results = svc.match_transactions(profile.id, transactions, account.id)
        assert results[0]["status"] == "unmatched"

    def test_prevents_double_matching(self, test_db, profile, account):
        svc = ReconciliationService(test_db)
        test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-100.00,
            income_date="2025-03-01",
            budget_item_id=None,
        )
        # Two identical transactions — only one can match the single item
        transactions = [
            {"date": "2025-03-15", "amount": 100.00, "description": "First"},
            {"date": "2025-03-15", "amount": 100.00, "description": "Second"},
        ]
        results = svc.match_transactions(profile.id, transactions, account.id)
        matched = [r for r in results if r["status"] == "matched"]
        unmatched = [r for r in results if r["status"] == "unmatched"]
        assert len(matched) == 1
        assert len(unmatched) == 1

    def test_skips_already_paid_items(self, test_db, profile, account):
        svc = ReconciliationService(test_db)
        # Create a paid extrapolation item (has ledger_entry_id)
        item = test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-100.00,
            income_date="2025-03-01",
            budget_item_id=None,
        )
        # Simulate linking a ledger entry
        test_db.update_extrapolation_item_ledger_id(item.id, 999)

        transactions = [{"date": "2025-03-15", "amount": 100.00, "description": "Paid"}]
        results = svc.match_transactions(profile.id, transactions, account.id)
        assert results[0]["status"] == "unmatched"


class TestReconciliationImportConfirmed:
    """Tests for ReconciliationService.import_confirmed."""

    def test_import_with_extrapolation_link(self, test_db, profile, account):
        svc = ReconciliationService(test_db)
        # Create an unpaid extrapolation item
        item = test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-100.00,
            income_date="2025-03-01",
            budget_item_id=None,
        )
        confirmed = [{
            "transaction": {"date": "2025-03-15", "amount": 100.00, "description": "Rent"},
            "extrapolation_item_id": item.id,
        }]
        result = svc.import_confirmed(profile.id, account.id, confirmed)
        assert result["imported"] == 1
        assert result["linked"] == 1

        # Verify the extrapolation item now has a ledger_entry_id
        updated_item = test_db.get_extrapolation_item(item.id)
        assert updated_item.ledger_entry_id is not None

    def test_import_standalone_no_extrap(self, test_db, profile, account):
        svc = ReconciliationService(test_db)
        confirmed = [{
            "transaction": {"date": "2025-03-15", "amount": 42.00, "description": "Coffee"},
            "extrapolation_item_id": None,
        }]
        result = svc.import_confirmed(profile.id, account.id, confirmed)
        assert result["imported"] == 1
        assert result["linked"] == 0

        # Verify a ledger entry was created
        entries = test_db.fetch_ledger_items(account.id)
        # Account creation itself creates a Starting Balance entry
        amounts = [e.amount for e in entries]
        assert 42.00 in amounts


# ===========================================================================
# LedgerService
# ===========================================================================

class TestLedgerServiceCreate:
    """Tests for LedgerService.create_ledger_entry."""

    def test_create_with_string_dates(self, test_db, account):
        svc = LedgerService(test_db)
        entry = svc.create_ledger_entry(
            account_id=account.id,
            amount=200.00,
            paid_date="2025-03-10",
            income_date="2025-03-01",
            name="Test Payment",
        )
        assert entry.id is not None
        assert entry.amount == 200.00
        assert entry.name == "Test Payment"

    def test_create_with_date_objects(self, test_db, account):
        svc = LedgerService(test_db)
        entry = svc.create_ledger_entry(
            account_id=account.id,
            amount=150.00,
            paid_date=date(2025, 3, 10),
            income_date=date(2025, 3, 1),
            name="Date Object Payment",
        )
        assert entry.id is not None
        assert entry.amount == 150.00

    def test_create_with_iso_datetime_string(self, test_db, account):
        svc = LedgerService(test_db)
        entry = svc.create_ledger_entry(
            account_id=account.id,
            amount=75.00,
            paid_date="2025-03-10T14:30:00",
            income_date="2025-03-01T00:00:00",
            name="DateTime String",
        )
        assert entry.id is not None


class TestLedgerServiceMarkPaid:
    """Tests for LedgerService.mark_extrapolation_item_paid."""

    def test_marks_item_paid(self, test_db, profile, account):
        svc = LedgerService(test_db)
        item = test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-100.00,
            income_date="2025-03-01",
            budget_item_id=None,
        )
        entry = svc.mark_extrapolation_item_paid(
            extrapolation_item_id=item.id,
            account_id=account.id,
            paid_date="2025-03-15",
        )
        assert entry.id is not None
        # Verify link
        updated = test_db.get_extrapolation_item(item.id)
        assert updated.ledger_entry_id == entry.id

    def test_rejects_already_paid(self, test_db, profile, account):
        svc = LedgerService(test_db)
        item = test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-100.00,
            income_date="2025-03-01",
            budget_item_id=None,
        )
        # Pay it once
        svc.mark_extrapolation_item_paid(item.id, account.id, "2025-03-15")
        # Second attempt should raise
        with pytest.raises(ValueError, match="already marked as paid"):
            svc.mark_extrapolation_item_paid(item.id, account.id, "2025-03-16")

    def test_savings_items_use_abs_amount(self, test_db, profile, account):
        svc = LedgerService(test_db)
        item = test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-200.00,  # Negative (outflow from spending pool)
            income_date="2025-03-01",
            budget_item_id=None,
            category="savings",
        )
        entry = svc.mark_extrapolation_item_paid(item.id, account.id, "2025-03-15")
        # Savings deposits should be positive (abs of negative amount)
        assert entry.amount == 200.00

    def test_non_savings_preserves_sign(self, test_db, profile, account):
        svc = LedgerService(test_db)
        item = test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=-150.00,
            income_date="2025-03-01",
            budget_item_id=None,
            category=None,
        )
        entry = svc.mark_extrapolation_item_paid(item.id, account.id, "2025-03-15")
        assert entry.amount == -150.00

    def test_not_found_raises(self, test_db, account):
        svc = LedgerService(test_db)
        with pytest.raises(ValueError, match="not found"):
            svc.mark_extrapolation_item_paid(99999, account.id)


class TestLedgerServiceDelete:
    """Tests for LedgerService.delete_ledger_entry (balance reversal)."""

    def test_delete_reverses_entry(self, test_db, account):
        svc = LedgerService(test_db)
        entry = svc.create_ledger_entry(
            account_id=account.id,
            amount=500.00,
            paid_date="2025-03-10",
            income_date="2025-03-01",
            name="To Delete",
        )
        assert entry.id is not None
        svc.delete_ledger_entry(entry.id)
        # Entry should be gone
        fetched = test_db.get_ledger_entry(entry.id)
        assert fetched is None

    def test_delete_nonexistent_does_not_crash(self, test_db):
        svc = LedgerService(test_db)
        # Should not raise
        svc.delete_ledger_entry(99999)


# ===========================================================================
# AccountService
# ===========================================================================

class TestAccountServiceBalance:
    """Tests for AccountService.get_account_balance."""

    def test_sums_ledger_entries(self, test_db, profile, account):
        svc = AccountService(test_db)
        ledger_svc = LedgerService(test_db)

        ledger_svc.create_ledger_entry(account.id, 100.00, "2025-03-01", "2025-03-01", "Income")
        ledger_svc.create_ledger_entry(account.id, -30.00, "2025-03-02", "2025-03-01", "Expense")

        balance = svc.get_account_balance(account.id)
        # Starting Balance (0) + 100 + (-30) = 70
        assert balance == 70.00

    def test_returns_zero_with_no_manual_entries(self, test_db, profile):
        svc = AccountService(test_db)
        # Create account with balance=0 (Starting Balance entry = 0)
        acct = test_db.create_account(profile.id, "Empty", "checking", 0)
        balance = svc.get_account_balance(acct.id)
        assert balance == 0.0

    def test_returns_zero_for_nonexistent_account(self, test_db):
        svc = AccountService(test_db)
        # No account 99999 — fetch_ledger_items returns empty list
        balance = svc.get_account_balance(99999)
        assert balance == 0.0

    def test_balance_with_starting_balance(self, test_db, profile):
        svc = AccountService(test_db)
        # Account with balance=500 creates a Starting Balance ledger entry of 500
        acct = test_db.create_account(profile.id, "Savings", "savings", 500)
        balance = svc.get_account_balance(acct.id)
        assert balance == 500.0


# ===========================================================================
# DebtService
# ===========================================================================

class TestDebtServiceComputePayments:
    """Tests for DebtService.compute_debt_payments."""

    def test_no_debts_returns_empty(self, test_db, profile):
        svc = DebtService(test_db)
        result = svc.compute_debt_payments(profile.id, savings_margin=50.0)
        assert result == []

    def test_paid_off_debts_ignored(self, test_db, profile):
        svc = DebtService(test_db)
        # Debt with remaining_amount = 0 should be ignored
        test_db.create_debt(
            profileId=profile.id,
            name="Paid Off Card",
            total_amount=1000.00,
            remaining_amount=0.00,
            min_payment=25.00,
            interest_rate=0.20,
        )
        result = svc.compute_debt_payments(profile.id, savings_margin=50.0)
        assert result == []


class TestDebtServiceSavePayments:
    """Tests for DebtService.save_debt_payments."""

    def test_creates_extrapolation_items(self, test_db, profile):
        svc = DebtService(test_db)
        payments = [
            {"debt_id": 1, "debt_name": "Visa", "amount": 200.00, "income_date": "2025-03-15"},
            {"debt_id": 2, "debt_name": "MC", "amount": 100.00, "income_date": "2025-03-15"},
        ]
        count = svc.save_debt_payments(profile.id, payments)
        assert count == 2

        items = test_db.fetch_extrapolation_items(profile.id)
        debt_items = [i for i in items if i.category == "debt_payment"]
        assert len(debt_items) == 2
        # Amounts should be negative (expenses)
        for item in debt_items:
            assert item.amount < 0

    def test_empty_payments_returns_zero(self, test_db, profile):
        svc = DebtService(test_db)
        count = svc.save_debt_payments(profile.id, [])
        assert count == 0


# ===========================================================================
# AIService
# ===========================================================================

class TestAIServiceExtractContent:
    """Tests for AIService._extract_content."""

    def setup_method(self):
        self.svc = AIService.__new__(AIService)

    def test_openai_format(self):
        data = {
            "choices": [
                {"message": {"content": "Budget looks good!"}}
            ]
        }
        assert self.svc._extract_content(data) == "Budget looks good!"

    def test_ollama_native_format(self):
        data = {
            "message": {"content": "Analysis from Ollama"}
        }
        assert self.svc._extract_content(data) == "Analysis from Ollama"

    def test_ollama_generate_format(self):
        data = {"response": "Generated text here"}
        assert self.svc._extract_content(data) == "Generated text here"

    def test_fallback_to_raw_string(self):
        data = {"unexpected_key": "some value"}
        result = self.svc._extract_content(data)
        # Falls back to JSON dump
        assert "unexpected_key" in result
        assert "some value" in result

    def test_openai_choice_with_content_directly(self):
        data = {"choices": [{"content": "Direct content"}]}
        assert self.svc._extract_content(data) == "Direct content"

    def test_openai_choice_as_string(self):
        data = {"choices": ["plain string response"]}
        assert self.svc._extract_content(data) == "plain string response"

    def test_empty_choices_falls_through(self):
        data = {"choices": []}
        # Empty choices list — should fall through to last-resort JSON dump
        result = self.svc._extract_content(data)
        assert "choices" in result


class TestAIServiceConfig:
    """Tests for AIService.get_config / save_config."""

    def test_get_config_defaults(self, test_db):
        svc = AIService(test_db)
        config = svc.get_config()
        assert config["server_url"] == ""
        assert config["model"] == "qwen2.5:0.5b"
        assert config["enabled"] is False

    def test_save_and_get_config(self, test_db):
        svc = AIService(test_db)
        svc.save_config(
            server_url="http://localhost:11434/v1",
            model="llama3",
            enabled=True,
        )
        config = svc.get_config()
        assert config["server_url"] == "http://localhost:11434/v1"
        assert config["model"] == "llama3"
        assert config["enabled"] is True

    def test_save_config_overwrite(self, test_db):
        svc = AIService(test_db)
        svc.save_config("http://old", "old-model", True)
        svc.save_config("http://new", "new-model", False)
        config = svc.get_config()
        assert config["server_url"] == "http://new"
        assert config["model"] == "new-model"
        assert config["enabled"] is False


class TestAIServiceBuildSummary:
    """Tests for AIService.build_budget_summary."""

    def test_includes_column_data(self, test_db, profile):
        svc = AIService(test_db)
        # Create some extrapolation items so the schedule has data
        test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=2000.00,
            income_date="2025-03-15",
            budget_item_id=None,
            category=None,
        )
        test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-20",
            amount=-500.00,
            income_date="2025-03-15",
            budget_item_id=None,
            category=None,
        )
        summary = svc.build_budget_summary(profile.id)
        assert "EXTRAPOLATION SCHEDULE" in summary

    def test_flags_negative_balances(self, test_db, profile):
        svc = AIService(test_db)
        # Create items that produce a negative balance column
        test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-15",
            amount=100.00,
            income_date="2025-03-15",
            budget_item_id=None,
        )
        test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-16",
            amount=-500.00,
            income_date="2025-03-15",
            budget_item_id=None,
        )
        summary = svc.build_budget_summary(profile.id)
        assert "NEGATIVE BALANCE" in summary

    def test_empty_schedule(self, test_db, profile):
        svc = AIService(test_db)
        summary = svc.build_budget_summary(profile.id)
        # Should still produce header text even with no data
        assert "EXTRAPOLATION SCHEDULE" in summary


# ===========================================================================
# CalendarService
# ===========================================================================

class TestCalendarServiceAddOneOff:
    """Tests for CalendarService.add_one_off_item."""

    def test_unpaid_creates_extrapolation_item(self, test_db, profile, account):
        svc = CalendarService(test_db)
        result = svc.add_one_off_item(
            profile_id=profile.id,
            name="Emergency Expense",
            amount=-150.00,
            item_type="Expense",
            income_date="2025-03-15",
            is_paid=False,
        )
        assert result["type"] == "extrapolation"
        assert result["item"].category == "one_off"

    def test_paid_creates_ledger_entry(self, test_db, profile, account):
        svc = CalendarService(test_db)
        result = svc.add_one_off_item(
            profile_id=profile.id,
            name="Refund",
            amount=50.00,
            item_type="Income",
            income_date="2025-03-15",
            account_id=account.id,
            is_paid=True,
        )
        assert result["type"] == "ledger"
        assert result["entry"].amount == 50.00

    def test_paid_without_account_creates_extrapolation(self, test_db, profile):
        """When is_paid=True but no account_id, falls through to extrapolation."""
        svc = CalendarService(test_db)
        result = svc.add_one_off_item(
            profile_id=profile.id,
            name="No Account",
            amount=-25.00,
            item_type="Expense",
            is_paid=True,
            account_id=None,
        )
        assert result["type"] == "extrapolation"


class TestCalendarServiceSaveSavings:
    """Tests for CalendarService.save_computed_savings."""

    def test_creates_negative_extrapolation_items(self, test_db, profile):
        svc = CalendarService(test_db)
        entries = [
            {"date": "2025-03-15", "amount": 200.00},
            {"date": "2025-04-01", "amount": 100.00},
        ]
        count = svc.save_computed_savings(profile.id, entries)
        assert count == 2

        items = test_db.fetch_extrapolation_items(profile.id)
        savings = [i for i in items if i.category == "savings"]
        assert len(savings) == 2
        # Amounts should be negative (transfer out of spending)
        for item in savings:
            assert item.amount < 0

    def test_empty_list(self, test_db, profile):
        svc = CalendarService(test_db)
        count = svc.save_computed_savings(profile.id, [])
        assert count == 0


class TestCalendarServiceFixUnscheduled:
    """Tests for CalendarService.fix_unscheduled_items."""

    def test_assigns_income_dates(self, test_db, profile):
        svc = CalendarService(test_db)
        # Create items without income_date
        item1 = test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-20",
            amount=-50.00,
            income_date=None,
            budget_item_id=None,
        )
        item2 = test_db.create_extrapolation_item(
            profileId=profile.id,
            date="2025-03-25",
            amount=-75.00,
            income_date=None,
            budget_item_id=None,
        )
        count = svc.fix_unscheduled_items([
            {"id": item1.id, "income_date": "2025-03-15"},
            {"id": item2.id, "income_date": "2025-03-15"},
        ])
        assert count == 2


# ===========================================================================
# ProfileService
# ===========================================================================

class TestProfileService:
    """Tests for ProfileService basic operations."""

    def test_create_and_list(self, test_db):
        svc = ProfileService(test_db)
        p = svc.create_profile("My Budget")
        assert p.id is not None
        assert p.name == "My Budget"

        all_profiles = svc.get_all_profiles()
        assert any(pr.id == p.id for pr in all_profiles)

    def test_delete(self, test_db):
        svc = ProfileService(test_db)
        p = svc.create_profile("To Delete")
        svc.delete_profile(p.id)
        all_profiles = svc.get_all_profiles()
        assert not any(pr.id == p.id for pr in all_profiles)
