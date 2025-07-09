from datetime import date

from database.budget_item import BudgetItem
from database.database import Database
from shedule.schedule import Schedule
from shedule.schedule_column import ScheduleColumn
from shedule.schedule_entry import ScheduleEntry
from .base import BaseScheduler


class DefaultKnapsack(BaseScheduler):
    push_expenses_up: bool = False
    profile_id: int = None
    start_date: date = None
    end_date: date = None
    schedule: Schedule = None
    database: Database = None
    income_budget_items: list[BudgetItem] = None
    expense_budget_items: list[BudgetItem] = None

    def __init__(self, database, profile_id):
        super().__init__(database, profile_id)
        self.push_expenses_up = False
        self.income_budget_items = []
        self.expense_budget_items = []
        self.unscheduled_schedule_entries: list[ScheduleEntry] = []
        for budget_item in self.budget_items:
            if budget_item.type == "Income":
                self.income_budget_items.append(budget_item)
            else:
                self.expense_budget_items.append(budget_item)

    def build_input_date_columns(self):
        # for each income
        raw_dates = []
        for budget_item in self.income_budget_items:
            for period in budget_item.periods:
                period_dates = self.compute_item_period_dates(
                    period, self.start_date, self.end_date
                )
                for date in period_dates:
                    # add schedule entry to column in incomes
                    income_entry = ScheduleEntry()
                    income_entry.amount = budget_item.amount
                    income_entry.income_date = date
                    income_entry.due_date = date
                    income_entry.name = budget_item.name
                    income_entry.type = budget_item.type
                    income_entry.budget_item_id = budget_item.id
                    date_key = date.strftime("%Y-%m-%d")
                    if date_key not in self.schedule.columns:
                        self.schedule.columns[date_key] = ScheduleColumn()
                        self.schedule.columns[date_key].income_date = date
                    self.schedule.columns[date_key].add_income(income_entry)

                raw_dates.extend(period_dates)
        self.schedule.sorted_income_dates = sorted(list(set(raw_dates)))

    def build_unscheduled_schedule_entries(self):
        for expense_budget_item in self.expense_budget_items:
            for period in expense_budget_item.periods:
                period_dates = self.compute_item_period_dates(
                    period, self.start_date, self.end_date
                )
                for date in period_dates:
                    entry = ScheduleEntry()
                    entry.amount = -expense_budget_item.amount
                    entry.income_date = None
                    entry.due_date = date
                    entry.name = expense_budget_item.name
                    entry.type = expense_budget_item.type
                    entry.budget_item_id = expense_budget_item.id
                    self.unscheduled_schedule_entries.append(entry)

    def schedule_expense_entry(self, entry: ScheduleEntry):
        income_date = None
        for in_date in self.schedule.sorted_income_dates:
            up_to = self.schedule.get_total_as_of(in_date)
            expense_amount = float(entry.amount)
            if self.push_expenses_up and expense_amount <= up_to:
                income_date = in_date
                break

            if in_date < entry.due_date and expense_amount <= up_to:
                income_date = in_date

            if in_date >= entry.due_date:
                break

        return income_date

    def schedule_expense_entries_pass(self, schedule_entries):
        unscheduled = []
        for entry in schedule_entries:
            income_date = self.schedule_expense_entry(entry)
            if income_date is not None:
                self.schedule.columns[income_date.strftime("%Y-%m-%d")].expenses.append(
                    entry
                )
            else:
                unscheduled.append(entry)
        return unscheduled

    def run(self, start_date: date, end_date: date):
        super().run(start_date, end_date)
        self.build_input_date_columns()
        self.build_unscheduled_schedule_entries()

        # // TODO: find overridden and paid by ledger items, fit those in to the scheduling
        # let unscheduled = this.scheduleExpenseEntriesPass(scheduleEntries);
        unscheduled = self.schedule_expense_entries_pass(
            self.unscheduled_schedule_entries
        )

        # push up unscheduled to find spots if possible
        self.push_expenses_up = True
        unscheduled = self.schedule_expense_entries_pass(unscheduled)

        # // admit to our losses? should check if needed I guess
        self.schedule.unscheduled_entries = unscheduled
