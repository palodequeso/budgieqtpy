from datetime import date, timedelta
from database.account import Account
from database.budget_group import BudgetGroup
from database.budget_item_period import BudgetItemPeriod
from database.extrapolation_item import ExtrapolationItem
from shedule.schedule import Schedule
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
        self.start_date = start_date
        self.end_date = end_date

    def compute_savings(self):
        return []

    def compute_item_period_dates(self, period: BudgetItemPeriod, start_date, end_date):
        dates = []
        if period.type == "Daily":
            days = (end_date - start_date).days + 1
            for i in range(days):
                dates.append(start_date + timedelta(days=i))
        elif period.type == "Weekly":
            weeks = math.ceil(((end_date - start_date).days + 1) / 7)
            for i in range(weeks):
                dates.append(start_date + timedelta(weeks=i))
        elif period.type == "Biweekly":
            biweeks = math.ceil(((end_date - start_date).days + 1) / 14)
            for i in range(biweeks):
                dates.append(start_date + timedelta(weeks=i * 2))
        elif period.type == "Monthly":
            months = math.ceil(((end_date - start_date).days + 1) / 30)
            for i in range(months):
                date_diff = start_date + timedelta(days=i * 30)
                period_day = 0
                if period.value == "Last":
                    period_day = LAST_DAY_OF_MONTH[date_diff.month]
                else:
                    period_day = int(re.sub(r"[^0-9]", "", period.value))
                new_date = date(date_diff.year, date_diff.month, period_day)
                if period.business_day == "Previous":
                    days_to_subtract = new_date.weekday() - 5
                    if days_to_subtract > 0:
                        new_date = new_date - timedelta(days=days_to_subtract)
                elif period.business_day == "Next":
                    days_to_add = 5 - new_date.weekday()
                    if days_to_add > 0:
                        new_date = new_date + timedelta(days=days_to_add)
                dates.append(new_date)
        elif period.type == "Business Days":
            days = (end_date - start_date).days + 1
            for i in range(days):
                if start_date + timedelta(days=i).weekday() < 5:
                    dates.append(start_date + timedelta(days=i))
        return dates
