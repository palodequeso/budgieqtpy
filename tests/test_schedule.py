import unittest
from datetime import date, datetime, timedelta
from database.account import Account
from database.budget_item import BudgetItem
from database.budget_item_period import BudgetItemPeriod
from database.extrapolation_item import ExtrapolationItem
from database.ledger_entry import LedgerEntry
from shedule.schedule import Schedule


class TestSchedule(unittest.TestCase):
    def test_build_schedule(self):
        schedule = Schedule()
        schedule.build_schedule()
        self.assertEqual(schedule.starting_balance, 0)

        schedule.clear()
        schedule.accounts = [
            Account(
                name="test",
                account_type="Checking",
                id=1,
                created_at=date.today(),
                updated_at=date.today(),
            )
        ]
        schedule.ledger_entries_by_account[1] = [
            LedgerEntry(
                id=2,
                name="test-ledger",
                paid_date=datetime.now(),
                income_date=date.today(),
                type="Income",
                amount=100,
                account_id=1,
                created_at=date.today(),
                updated_at=date.today(),
            )
        ]
        schedule.ledger_entries_by_id[2] = schedule.ledger_entries_by_account[1][0]
        schedule.budget_item_list = [
            BudgetItem(
                id=3,
                name="test-budget-item",
                type="Income",
                created_at=date.today(),
                updated_at=date.today(),
                amount=1000,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=365),
                budget_group_id=1,
                periods=[
                    BudgetItemPeriod(
                        type="Monthly",
                        value=1,
                        business_day="None",
                        budget_item_id=3,
                        id=4,
                        created_at=date.today(),
                        updated_at=date.today(),
                    )
                ],
            )
        ]
        schedule.budget_items[3] = schedule.budget_item_list[0]
        for i in range(12):
            income_date = date.today() + timedelta(days=i * 30)
            extrapolation_item = ExtrapolationItem(
                due_date=income_date,
                amount=1000,
                income_date=income_date,
                budget_item_id=3,
                id=5,
                created_at=date.today(),
                updated_at=date.today(),
            )
            schedule.extrapolation_items.append(extrapolation_item)

        schedule.build_schedule()

        self.assertEqual(len(schedule.sorted_income_dates), 12)
        self.assertEqual(schedule.sorted_income_dates[0], date.today())
        self.assertEqual(schedule.sorted_income_dates[11], date.today() + timedelta(days=330))
