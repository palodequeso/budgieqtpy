from datetime import date, timedelta
from database.account import Account
from database.budget_group import BudgetGroup
from database.budget_item_period import BudgetItemPeriod
from database.extrapolation_item import ExtrapolationItem
from shedule.schedule import Schedule
import calendar
import math
import re

LAST_DAY_OF_MONTH = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}


class BaseScheduler:
    profile_id: int = None
    start_date: date = None
    end_date: date = None
    schedule: Schedule = None
    database: object = None
    accounts: list[Account] = None
    budget_groups: list[BudgetGroup] = None

    def __init__(self, database, profile_id):
        self.start_date = None
        self.end_date = None
        self.schedule = Schedule()
        self.database = database
        self.profile_id = profile_id
        self.accounts = self.database.fetch_accounts(self.profile_id)
        self.budget_groups = self.database.fetch_budget_groups(self.profile_id)
        self.budget_items = self.database.fetch_budget_items(self.profile_id)

    def save_schedule(self):
        self.database.clear_extrapolation_items(self.profile_id)
        for income_date in self.schedule.sorted_income_dates:
            income_key = income_date.strftime("%Y-%m-%d")
            for income in self.schedule.columns[income_key].incomes:
                self.database.create_extrapolation_item(
                    self.profile_id,
                    income.due_date,
                    income.amount,
                    income_date,
                    income.budget_item_id,
                )
            for expense in self.schedule.columns[income_key].expenses:
                self.database.create_extrapolation_item(
                    self.profile_id,
                    expense.due_date,
                    expense.amount,
                    income_date,
                    expense.budget_item_id,
                )

    def get_starting_balance(self):
        return 0.0

    def run(self, start_date: date, end_date: date):
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be before or equal to end_date ({end_date})")
        self.start_date = start_date
        self.end_date = end_date

    def compute_savings(self):
        return []

    def compute_item_period_dates(self, period: BudgetItemPeriod, start_date, end_date):
        dates = []
        if period.type == "Daily":
            days = (end_date - start_date).days + 1
            for i in range(days):
                new_date = start_date + timedelta(days=i)
                if new_date >= start_date:  # Only include dates >= start_date
                    dates.append(new_date)
        elif period.type == "Weekly":
            weeks = math.ceil(((end_date - start_date).days + 1) / 7)
            for i in range(weeks):
                new_date = start_date + timedelta(weeks=i)
                if new_date >= start_date:
                    dates.append(new_date)
        elif period.type == "Biweekly":
            biweeks = math.ceil(((end_date - start_date).days + 1) / 14)
            for i in range(biweeks):
                new_date = start_date + timedelta(weeks=i * 2)
                if new_date >= start_date:
                    dates.append(new_date)
        elif period.type == "Monthly":
            # Iterate by (year, month) to avoid duplicates from approximate day math
            year = start_date.year
            month = start_date.month
            while True:
                period_day = 0
                if period.value == "Last":
                    # Use calendar.monthrange to get correct last day (handles leap years)
                    period_day = calendar.monthrange(year, month)[1]
                else:
                    period_day = int(re.sub(r"[^0-9]", "", period.value))
                    # Ensure day is valid for the month (e.g., Feb 30 -> Feb 28/29)
                    max_day = calendar.monthrange(year, month)[1]
                    period_day = min(period_day, max_day)
                new_date = date(year, month, period_day)
                if period.business_day == "Previous":
                    # If Saturday (5) or Sunday (6), move to previous Friday
                    if new_date.weekday() == 5:  # Saturday
                        new_date = new_date - timedelta(days=1)
                    elif new_date.weekday() == 6:  # Sunday
                        new_date = new_date - timedelta(days=2)
                elif period.business_day == "Next":
                    # If Saturday (5) or Sunday (6), move to next Monday
                    if new_date.weekday() == 5:  # Saturday
                        new_date = new_date + timedelta(days=2)
                    elif new_date.weekday() == 6:  # Sunday
                        new_date = new_date + timedelta(days=1)
                if new_date > end_date:
                    break
                # Only include dates >= start_date
                if new_date >= start_date:
                    dates.append(new_date)
                # Advance to next month
                month += 1
                if month > 12:
                    month = 1
                    year += 1
        elif period.type == "Business Days":
            days = (end_date - start_date).days + 1
            for i in range(days):
                new_date = start_date + timedelta(days=i)
                if new_date >= start_date and new_date.weekday() < 5:
                    dates.append(new_date)
        return dates
