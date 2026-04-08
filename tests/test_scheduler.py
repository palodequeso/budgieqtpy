"""
Unit tests for the scheduler and schedule modules.

Covers:
- BaseScheduler.compute_item_period_dates (date computation, business day logic)
- DefaultKnapsack (knapsack algorithm, debt capping, scheduling passes)
- ScheduleColumn (income/expense/total math)
- ScheduleEntry (totals, paid status, scheduled amounts)
- ScheduleWriter.col_letter (Excel-style column naming)
"""

import pytest
from datetime import date, timedelta

from database.budget_item import BudgetItem
from database.budget_item_period import BudgetItemPeriod
from database.database import Database
from database.extrapolation_item import ExtrapolationItem
from database.ledger_entry import LedgerEntry
from shedule.schedule import Schedule
from shedule.schedule_column import ScheduleColumn
from shedule.schedule_entry import ScheduleEntry
from shedule.schedule_entry_item import ScheduleEntryItem
from shedule.schedule_writer import ScheduleWriter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_period(type="Monthly", value="15th", business_day="None"):
    """Create a BudgetItemPeriod without touching the database."""
    return BudgetItemPeriod(
        type=type,
        value=value,
        business_day=business_day,
        budget_item_id=1,
    )


def _setup_db(tmp_path, income_amount=3000, expense_items=None):
    """
    Create an isolated SQLite database with a profile, group, one income item,
    and optional expense items.  Returns (Database, profile_id).

    Each income item is Monthly on the 1st (no business-day adjustment).
    expense_items is a list of dicts:
        [{"name": "Rent", "amount": 1200, "period_day": "1st"}, ...]
    """
    import os
    os.environ["DATABASE_PATH"] = str(tmp_path / "test.db")

    db = Database(str(tmp_path / "test.db"))
    profile = db.create_profile("Test")
    profile_id = profile.id
    group = db.create_budget_group(profile_id, "Bills")

    # Income — monthly on the 1st
    income_period = BudgetItemPeriod("Monthly", "1st", "None", None)
    db.create_budget_item(
        profile_id,
        "Salary",
        "Income",
        income_amount,
        group.id,
        date(2026, 1, 1),
        date(2026, 12, 31),
        [income_period],
    )

    if expense_items:
        for exp in expense_items:
            period_day = exp.get("period_day", "15th")
            period_type = exp.get("period_type", "Monthly")
            bday = exp.get("business_day", "None")
            debt_id = exp.get("debt_id", None)
            period = BudgetItemPeriod(period_type, period_day, bday, None)
            db.create_budget_item(
                profile_id,
                exp["name"],
                "Expense",
                exp["amount"],
                group.id,
                date(2026, 1, 1),
                date(2026, 12, 31),
                [period],
                debt_id=debt_id,
            )

    return db, profile_id


# ===========================================================================
# BaseScheduler.compute_item_period_dates
# ===========================================================================

class TestComputeItemPeriodDates:
    """Tests for BaseScheduler.compute_item_period_dates via DefaultKnapsack."""

    def _scheduler(self, tmp_path):
        """Return a minimal scheduler instance for calling compute_item_period_dates."""
        db, pid = _setup_db(tmp_path)
        from scheduler.default_knapsack import DefaultKnapsack
        return DefaultKnapsack(db, pid)

    # -- Monthly --

    def test_monthly_15th_correct_dates(self, tmp_path):
        sched = self._scheduler(tmp_path)
        period = _make_period("Monthly", "15th")
        dates = sched.compute_item_period_dates(
            period, date(2026, 1, 1), date(2026, 4, 30)
        )
        assert date(2026, 1, 15) in dates
        # All dates should fall on the 15th
        for d in dates:
            assert d.day == 15
        # Should produce at least 3 dates over a 4-month span
        assert len(dates) >= 3

    def test_monthly_last_correct_month_end(self, tmp_path):
        sched = self._scheduler(tmp_path)
        period = _make_period("Monthly", "Last")
        dates = sched.compute_item_period_dates(
            period, date(2026, 1, 1), date(2026, 4, 30)
        )
        # Each date should be the last day of its respective month
        for d in dates:
            import calendar
            _, last = calendar.monthrange(d.year, d.month)
            assert d.day == last, f"{d} is not the last day of its month (expected {last})"
        assert len(dates) >= 3

    def test_monthly_last_leap_year(self, tmp_path):
        sched = self._scheduler(tmp_path)
        period = _make_period("Monthly", "Last")
        # 2028 is a leap year — end_date must include the 29th
        dates = sched.compute_item_period_dates(
            period, date(2028, 2, 1), date(2028, 2, 29)
        )
        assert any(d.day == 29 for d in dates), "Leap year Feb should end on 29"

    def test_monthly_1st_previous_business_day(self, tmp_path):
        """2026-02-01 is a Sunday, should shift to Friday 2026-01-30."""
        sched = self._scheduler(tmp_path)
        period = _make_period("Monthly", "1st", "Previous")
        dates = sched.compute_item_period_dates(
            period, date(2026, 1, 25), date(2026, 2, 28)
        )
        # Feb 1 2026 is Sunday -> Previous = Friday Jan 30
        friday = date(2026, 1, 30)
        assert friday in dates, f"Expected {friday} in {dates}"
        assert friday.weekday() == 4  # Friday

    def test_monthly_15th_next_business_day(self, tmp_path):
        """2026-02-15 is a Sunday, should shift to Monday 2026-02-16."""
        sched = self._scheduler(tmp_path)
        period = _make_period("Monthly", "15th", "Next")
        dates = sched.compute_item_period_dates(
            period, date(2026, 2, 1), date(2026, 2, 28)
        )
        monday = date(2026, 2, 16)
        assert monday in dates, f"Expected {monday} in {dates}"
        assert monday.weekday() == 0  # Monday

    def test_monthly_saturday_previous_to_friday(self, tmp_path):
        """2026-08-15 is a Saturday, Previous should give Friday 2026-08-14."""
        sched = self._scheduler(tmp_path)
        period = _make_period("Monthly", "15th", "Previous")
        dates = sched.compute_item_period_dates(
            period, date(2026, 8, 1), date(2026, 8, 31)
        )
        friday = date(2026, 8, 14)
        assert friday in dates, f"Expected {friday} in {dates}"

    def test_monthly_saturday_next_to_monday(self, tmp_path):
        """2026-08-15 is a Saturday, Next should give Monday 2026-08-17."""
        sched = self._scheduler(tmp_path)
        period = _make_period("Monthly", "15th", "Next")
        dates = sched.compute_item_period_dates(
            period, date(2026, 8, 1), date(2026, 8, 31)
        )
        monday = date(2026, 8, 17)
        assert monday in dates, f"Expected {monday} in {dates}"

    # -- Weekly --

    def test_weekly_dates_7_days_apart(self, tmp_path):
        sched = self._scheduler(tmp_path)
        period = _make_period("Weekly", "")
        start = date(2026, 3, 1)
        end = date(2026, 3, 31)
        dates = sched.compute_item_period_dates(period, start, end)
        assert len(dates) >= 4
        for i in range(1, len(dates)):
            assert (dates[i] - dates[i - 1]).days == 7

    # -- Biweekly --

    def test_biweekly_dates_14_days_apart(self, tmp_path):
        sched = self._scheduler(tmp_path)
        period = _make_period("Biweekly", "")
        start = date(2026, 1, 1)
        end = date(2026, 2, 28)
        dates = sched.compute_item_period_dates(period, start, end)
        assert len(dates) >= 3
        for i in range(1, len(dates)):
            assert (dates[i] - dates[i - 1]).days == 14

    # -- Daily --

    def test_daily_one_per_day(self, tmp_path):
        sched = self._scheduler(tmp_path)
        period = _make_period("Daily", "")
        start = date(2026, 3, 1)
        end = date(2026, 3, 7)
        dates = sched.compute_item_period_dates(period, start, end)
        assert len(dates) == 7
        for i in range(1, len(dates)):
            assert (dates[i] - dates[i - 1]).days == 1

    # -- Edge: empty range --

    def test_end_before_start_returns_empty(self, tmp_path):
        sched = self._scheduler(tmp_path)
        period = _make_period("Monthly", "15th")
        dates = sched.compute_item_period_dates(
            period, date(2026, 6, 1), date(2026, 5, 1)
        )
        assert dates == []

    # -- Business Days --

    def test_business_days_excludes_weekends(self, tmp_path):
        sched = self._scheduler(tmp_path)
        period = _make_period("Business Days", "")
        # Mon Mar 2 to Sun Mar 8, 2026
        start = date(2026, 3, 2)
        end = date(2026, 3, 8)
        dates = sched.compute_item_period_dates(period, start, end)
        for d in dates:
            assert d.weekday() < 5, f"{d} is a weekend day"
        assert len(dates) == 5


# ===========================================================================
# DefaultKnapsack
# ===========================================================================

class TestDefaultKnapsack:

    def test_build_input_date_columns(self, tmp_path):
        """Income items produce the right column structure."""
        from scheduler.default_knapsack import DefaultKnapsack

        db, pid = _setup_db(tmp_path, income_amount=3000)
        dk = DefaultKnapsack(db, pid)
        dk.start_date = date(2026, 1, 1)
        dk.end_date = date(2026, 6, 30)
        dk.build_input_date_columns()

        # Should have columns for each income date (6-month span = at least 5)
        assert len(dk.schedule.columns) >= 5
        assert len(dk.schedule.sorted_income_dates) >= 5

        # Each column should have an income entry
        for d in dk.schedule.sorted_income_dates:
            col = dk.schedule.columns[d.strftime("%Y-%m-%d")]
            assert len(col.incomes) >= 1
            assert col.incomes[0].amount == 3000

    def test_build_unscheduled_schedule_entries(self, tmp_path):
        """Expense items become unscheduled entries with negative amounts."""
        from scheduler.default_knapsack import DefaultKnapsack

        db, pid = _setup_db(
            tmp_path,
            expense_items=[
                {"name": "Rent", "amount": 1200, "period_day": "1st"},
                {"name": "Utilities", "amount": 150, "period_day": "15th"},
            ],
        )
        dk = DefaultKnapsack(db, pid)
        dk.start_date = date(2026, 1, 1)
        dk.end_date = date(2026, 3, 31)
        dk.build_input_date_columns()
        dk.build_unscheduled_schedule_entries()

        # Should have entries for Rent and Utilities across ~3 months
        assert len(dk.unscheduled_schedule_entries) >= 6
        for entry in dk.unscheduled_schedule_entries:
            assert entry.amount < 0, "Expense entries should be negative"

    def test_build_unscheduled_debt_capped(self, tmp_path):
        """Debt-linked items are capped at remaining balance."""
        from scheduler.default_knapsack import DefaultKnapsack

        db, pid = _setup_db(tmp_path)
        # Create a debt with small remaining balance
        debt = db.create_debt(pid, "Car Loan", 10000, 250, 200, 5.0)

        # Create expense linked to that debt — payment of 200/month
        period = BudgetItemPeriod("Monthly", "1st", "None", None)
        group = db.create_budget_group(pid, "Debts")
        db.create_budget_item(
            pid, "Car Payment", "Expense", 200, group.id,
            date(2026, 1, 1), date(2026, 12, 31), [period],
            debt_id=debt.id,
        )

        dk = DefaultKnapsack(db, pid)
        dk.start_date = date(2026, 1, 1)
        dk.end_date = date(2026, 3, 31)
        dk.build_input_date_columns()
        dk.build_unscheduled_schedule_entries()

        # With remaining=250, first payment=200, second capped at 50, third skipped
        debt_entries = [
            e for e in dk.unscheduled_schedule_entries if e.name == "Car Payment"
        ]
        assert len(debt_entries) == 2, f"Expected 2 entries (250 remaining), got {len(debt_entries)}"
        amounts = sorted([abs(e.amount) for e in debt_entries], reverse=True)
        assert amounts[0] == 200
        assert amounts[1] == 50

    def test_schedule_expense_entry_assigns_correct_date(self, tmp_path):
        """An expense due on the 15th should be assigned to the 1st income column."""
        from scheduler.default_knapsack import DefaultKnapsack

        db, pid = _setup_db(
            tmp_path,
            income_amount=3000,
            expense_items=[{"name": "Rent", "amount": 1200, "period_day": "15th"}],
        )
        dk = DefaultKnapsack(db, pid)
        dk.start_date = date(2026, 1, 1)
        dk.end_date = date(2026, 1, 31)
        dk.build_input_date_columns()
        dk.build_unscheduled_schedule_entries()

        entry = dk.unscheduled_schedule_entries[0]
        income_date = dk.schedule_expense_entry(entry)
        assert income_date is not None, "Expense should be schedulable"
        assert income_date <= entry.due_date

    def test_schedule_expense_entry_returns_none_when_no_balance(self, tmp_path):
        """When no column has enough balance, returns None."""
        from scheduler.default_knapsack import DefaultKnapsack

        db, pid = _setup_db(
            tmp_path,
            income_amount=100,
            expense_items=[{"name": "BigBill", "amount": 5000, "period_day": "15th"}],
        )
        dk = DefaultKnapsack(db, pid)
        dk.start_date = date(2026, 1, 1)
        dk.end_date = date(2026, 1, 31)
        dk.build_input_date_columns()
        dk.build_unscheduled_schedule_entries()

        entry = dk.unscheduled_schedule_entries[0]
        income_date = dk.schedule_expense_entry(entry)
        assert income_date is None

    def test_schedule_expense_entries_pass_separates(self, tmp_path):
        """Pass separates scheduled from unscheduled entries."""
        from scheduler.default_knapsack import DefaultKnapsack

        db, pid = _setup_db(
            tmp_path,
            income_amount=1500,
            expense_items=[
                {"name": "Rent", "amount": 1200, "period_day": "15th"},
                {"name": "MegaBill", "amount": 5000, "period_day": "20th"},
            ],
        )
        dk = DefaultKnapsack(db, pid)
        dk.start_date = date(2026, 1, 1)
        dk.end_date = date(2026, 1, 31)
        dk.build_input_date_columns()
        dk.build_unscheduled_schedule_entries()

        unscheduled = dk.schedule_expense_entries_pass(dk.unscheduled_schedule_entries)

        # Rent (1200) fits in 1500, MegaBill (5000) does not
        rent_scheduled = any(
            e.name == "Rent"
            for col in dk.schedule.columns.values()
            for e in col.expenses
        )
        mega_unscheduled = any(e.name == "MegaBill" for e in unscheduled)
        assert rent_scheduled, "Rent should be scheduled"
        assert mega_unscheduled, "MegaBill should remain unscheduled"

    def test_full_run_income_and_expenses(self, tmp_path):
        """Full run() with income + expenses + two passes."""
        from scheduler.default_knapsack import DefaultKnapsack

        db, pid = _setup_db(
            tmp_path,
            income_amount=3000,
            expense_items=[
                {"name": "Rent", "amount": 1200, "period_day": "5th"},
                {"name": "Utilities", "amount": 150, "period_day": "15th"},
                {"name": "Insurance", "amount": 200, "period_day": "20th"},
            ],
        )
        dk = DefaultKnapsack(db, pid)
        dk.run(date(2026, 1, 1), date(2026, 6, 30))

        # Should have multiple income columns over 6 months
        assert len(dk.schedule.sorted_income_dates) >= 4

        # Total expenses scheduled should be > 0
        total_expenses = sum(
            len(col.expenses) for col in dk.schedule.columns.values()
        )
        assert total_expenses > 0

        # Unscheduled should be empty (all fit under 3000)
        assert len(dk.schedule.unscheduled_entries) == 0

    def test_run_raises_on_inverted_dates(self, tmp_path):
        """run() should raise ValueError when start > end."""
        from scheduler.default_knapsack import DefaultKnapsack

        db, pid = _setup_db(tmp_path)
        dk = DefaultKnapsack(db, pid)
        with pytest.raises(ValueError):
            dk.run(date(2026, 6, 1), date(2026, 5, 1))

    def test_dual_biweekly_income_alternating_weeks(self, tmp_path):
        """Two biweekly incomes on alternating weeks (family with two earners).

        Partner A is paid every other Friday starting Jan 2.
        Partner B is paid every other Friday starting Jan 9 (the off-week).
        Expenses should be distributed across all income columns so that
        every week has funds available.
        """
        import os
        from scheduler.default_knapsack import DefaultKnapsack

        os.environ["DATABASE_PATH"] = str(tmp_path / "test.db")
        db = Database(str(tmp_path / "test.db"))
        profile = db.create_profile("Family")
        pid = profile.id
        group = db.create_budget_group(pid, "Bills")

        # Partner A — biweekly starting Fri Jan 2 2026
        period_a = BudgetItemPeriod("Biweekly", "", "None", None)
        db.create_budget_item(
            pid, "Partner A Pay", "Income", 2000, group.id,
            date(2026, 1, 2), date(2026, 3, 31), [period_a],
        )

        # Partner B — biweekly starting Fri Jan 9 2026 (offset by 1 week)
        period_b = BudgetItemPeriod("Biweekly", "", "None", None)
        db.create_budget_item(
            pid, "Partner B Pay", "Income", 1800, group.id,
            date(2026, 1, 9), date(2026, 3, 31), [period_b],
        )

        # Expenses — due dates after the first income date (Jan 2)
        for exp in [
            {"name": "Rent", "amount": 1500, "period_day": "5th"},
            {"name": "Utilities", "amount": 200, "period_day": "15th"},
            {"name": "Groceries", "amount": 300, "period_day": "10th"},
        ]:
            period = BudgetItemPeriod("Monthly", exp["period_day"], "None", None)
            db.create_budget_item(
                pid, exp["name"], "Expense", exp["amount"], group.id,
                date(2026, 1, 1), date(2026, 3, 31), [period],
            )

        dk = DefaultKnapsack(db, pid)
        dk.run(date(2026, 1, 1), date(2026, 3, 31))

        # --- Income columns alternate weekly ---
        income_dates = dk.schedule.sorted_income_dates
        # Over ~13 weeks we expect ~6-7 dates from each partner
        assert len(income_dates) >= 6, f"Expected >=6 income dates, got {len(income_dates)}"

        # Verify alternation: consecutive income dates should be ~7 days apart
        for i in range(1, len(income_dates)):
            gap = (income_dates[i] - income_dates[i - 1]).days
            assert gap in (7, 14), (
                f"Gap between {income_dates[i-1]} and {income_dates[i]} is {gap} days, "
                "expected 7 (alternating) or 14 (same source)"
            )

        # Both partners should appear as income in columns
        partner_a_cols = 0
        partner_b_cols = 0
        for d in income_dates:
            col = dk.schedule.columns[d.strftime("%Y-%m-%d")]
            for inc in col.incomes:
                if inc.name == "Partner A Pay":
                    partner_a_cols += 1
                elif inc.name == "Partner B Pay":
                    partner_b_cols += 1
        assert partner_a_cols >= 3, f"Partner A should have >=3 pay dates, got {partner_a_cols}"
        assert partner_b_cols >= 3, f"Partner B should have >=3 pay dates, got {partner_b_cols}"

        # --- All expenses should be scheduled (total income >> total expenses) ---
        assert len(dk.schedule.unscheduled_entries) == 0, (
            f"All expenses should be schedulable but {len(dk.schedule.unscheduled_entries)} "
            "were left unscheduled"
        )

        # Each scheduled expense should land on or before its due date
        for col in dk.schedule.columns.values():
            for exp in col.expenses:
                assert col.income_date <= exp.due_date, (
                    f"Expense '{exp.name}' due {exp.due_date} was scheduled to "
                    f"income date {col.income_date} which is after its due date"
                )


# ===========================================================================
# ScheduleColumn
# ===========================================================================

class TestScheduleColumn:

    def _make_entry(self, amount):
        """Create a ScheduleEntry with a direct amount (scheduler mode)."""
        e = ScheduleEntry()
        e.amount = amount
        return e

    def test_income_total_sums_incomes(self):
        col = ScheduleColumn(date(2026, 1, 1), 0)
        col.add_income(self._make_entry(2000))
        col.add_income(self._make_entry(1000))
        assert col.income_total() == 3000

    def test_expenses_total_sums_expenses(self):
        col = ScheduleColumn(date(2026, 1, 1), 0)
        col.add_expense(self._make_entry(-500))
        col.add_expense(self._make_entry(-300))
        assert col.expenses_total() == -800

    def test_total_includes_starting_balance(self):
        col = ScheduleColumn(date(2026, 1, 1), 500)
        col.add_income(self._make_entry(2000))
        col.add_expense(self._make_entry(-800))
        # 500 + 2000 + (-800) = 1700
        assert col.total() == 1700

    def test_total_empty_column(self):
        col = ScheduleColumn(date(2026, 1, 1), 100)
        assert col.total() == 100


# ===========================================================================
# ScheduleEntry
# ===========================================================================

class TestScheduleEntry:

    def _make_extrap_item(self, amount):
        return ExtrapolationItem(
            due_date=date(2026, 1, 15),
            amount=amount,
            income_date=date(2026, 1, 1),
            budget_item_id=1,
        )

    def _make_ledger_entry(self, amount):
        from datetime import datetime
        return LedgerEntry(
            name="Test",
            paid_date=datetime(2026, 1, 15),
            income_date=datetime(2026, 1, 1),
            type="Expense",
            amount=amount,
            account_id=1,
        )

    def test_total_with_extrapolation_items(self):
        entry = ScheduleEntry("Expense", date(2026, 1, 1), None, [])
        entry.add_item(ScheduleEntryItem(self._make_extrap_item(-500)))
        entry.add_item(ScheduleEntryItem(self._make_extrap_item(-300)))
        assert entry.total() == -800

    def test_total_with_ledger_entries(self):
        """When ledger entries exist, total uses ledger amounts."""
        entry = ScheduleEntry("Expense", date(2026, 1, 1), None, [])
        item = ScheduleEntryItem(
            self._make_extrap_item(-500),
            self._make_ledger_entry(-475),
        )
        entry.add_item(item)
        # Should use ledger amount (-475), not extrapolation (-500)
        assert entry.total() == -475

    def test_total_with_direct_amount(self):
        """Scheduler mode: entry has amount but no items."""
        entry = ScheduleEntry()
        entry.amount = -1200
        assert entry.total() == -1200

    def test_all_paid_true_when_all_have_ledger(self):
        entry = ScheduleEntry("Expense", date(2026, 1, 1), None, [])
        entry.add_item(
            ScheduleEntryItem(
                self._make_extrap_item(-500),
                self._make_ledger_entry(-500),
            )
        )
        entry.add_item(
            ScheduleEntryItem(
                self._make_extrap_item(-300),
                self._make_ledger_entry(-300),
            )
        )
        assert entry.all_paid() is True

    def test_all_paid_false_when_some_unpaid(self):
        entry = ScheduleEntry("Expense", date(2026, 1, 1), None, [])
        entry.add_item(
            ScheduleEntryItem(
                self._make_extrap_item(-500),
                self._make_ledger_entry(-500),
            )
        )
        entry.add_item(ScheduleEntryItem(self._make_extrap_item(-300)))
        assert entry.all_paid() is False

    def test_all_paid_false_when_none_paid(self):
        entry = ScheduleEntry("Expense", date(2026, 1, 1), None, [])
        entry.add_item(ScheduleEntryItem(self._make_extrap_item(-500)))
        assert entry.all_paid() is False

    def test_scheduled_absolute_value(self):
        """scheduled() returns the absolute scheduled amount from extrapolation items."""
        entry = ScheduleEntry("Expense", date(2026, 1, 1), None, [])
        entry.add_item(ScheduleEntryItem(self._make_extrap_item(-500)))
        entry.add_item(ScheduleEntryItem(self._make_extrap_item(-300)))
        # scheduled() sums extrapolation amounts (not absolute for items mode)
        assert entry.scheduled() == -800

    def test_scheduled_direct_amount(self):
        """scheduled() with direct amount returns absolute value."""
        entry = ScheduleEntry()
        entry.amount = -1200
        assert entry.scheduled() == 1200

    def test_total_paid(self):
        entry = ScheduleEntry("Expense", date(2026, 1, 1), None, [])
        entry.add_item(
            ScheduleEntryItem(
                self._make_extrap_item(-500),
                self._make_ledger_entry(-500),
            )
        )
        entry.add_item(ScheduleEntryItem(self._make_extrap_item(-300)))
        assert entry.total_paid() == -500


# ===========================================================================
# ScheduleWriter.col_letter
# ===========================================================================

class TestColumnIndexToLetter:

    @pytest.fixture
    def writer(self):
        schedule = Schedule()
        return ScheduleWriter(schedule)

    @pytest.mark.parametrize(
        "num,expected",
        [
            (1, "A"),
            (2, "B"),
            (26, "Z"),
            (27, "AA"),
            (28, "AB"),
            (52, "AZ"),
            (53, "BA"),
            (702, "ZZ"),
            (703, "AAA"),
        ],
    )
    def test_column_letters(self, writer, num, expected):
        assert writer.col_letter(num) == expected


# ===========================================================================
# Schedule.get_total_as_of
# ===========================================================================

class TestScheduleGetTotalAsOf:

    def test_get_total_as_of_sums_columns(self):
        schedule = Schedule()
        schedule.starting_balance = 100

        col1 = ScheduleColumn(date(2026, 1, 1), 0)
        e1 = ScheduleEntry()
        e1.amount = 3000
        col1.add_income(e1)
        exp1 = ScheduleEntry()
        exp1.amount = -1200
        col1.add_expense(exp1)

        col2 = ScheduleColumn(date(2026, 2, 1), 0)
        e2 = ScheduleEntry()
        e2.amount = 3000
        col2.add_income(e2)
        exp2 = ScheduleEntry()
        exp2.amount = -1500
        col2.add_expense(exp2)

        schedule.columns["2026-01-01"] = col1
        schedule.columns["2026-02-01"] = col2
        schedule.sorted_income_dates = [date(2026, 1, 1), date(2026, 2, 1)]

        # As of Jan 1 (inclusive): 100 + 3000 + (-1200) = 1900
        assert schedule.get_total_as_of(date(2026, 1, 1)) == 1900.0

        # As of Feb 1 (inclusive): 1900 + 3000 + (-1500) = 3400
        assert schedule.get_total_as_of(date(2026, 2, 1)) == 3400.0

        # As of Jan 15 (between columns): only Jan column counted
        assert schedule.get_total_as_of(date(2026, 1, 15)) == 1900.0

    def test_get_total_as_of_no_income_dates(self):
        schedule = Schedule()
        schedule.starting_balance = 250
        assert schedule.get_total_as_of(date(2026, 1, 1)) == 250
