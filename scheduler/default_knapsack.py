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
                # Use budget item's own start_date as anchor for interval-based
                # periods (Weekly/Biweekly) so each item keeps its own cadence,
                # then clip to the scheduler's date range.
                item_start = max(budget_item.start_date, self.start_date)
                item_end = min(budget_item.end_date, self.end_date)
                period_dates = self.compute_item_period_dates(
                    period, item_start, item_end
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
        # Load debt balances for capping debt-linked budget items
        debt_remaining = {}
        if hasattr(self.database, 'fetch_debts'):
            for debt in self.database.fetch_debts(self.profile_id):
                debt_remaining[debt.id] = debt.remaining_amount

        for expense_budget_item in self.expense_budget_items:
            for period in expense_budget_item.periods:
                item_start = max(expense_budget_item.start_date, self.start_date)
                item_end = min(expense_budget_item.end_date, self.end_date)
                period_dates = self.compute_item_period_dates(
                    period, item_start, item_end
                )
                for date in period_dates:
                    # If linked to a debt, cap at remaining balance
                    debt_id = getattr(expense_budget_item, 'debt_id', None)
                    if debt_id and debt_id in debt_remaining:
                        if debt_remaining[debt_id] <= 0:
                            continue  # Debt fully paid off, skip
                        payment = min(expense_budget_item.amount, debt_remaining[debt_id])
                        debt_remaining[debt_id] -= payment
                    else:
                        payment = expense_budget_item.amount

                    entry = ScheduleEntry()
                    entry.amount = -payment
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
            # Expenses are stored as negative, so we need absolute value for comparison
            expense_amount = abs(float(entry.amount))
            if self.push_expenses_up and expense_amount <= up_to:
                income_date = in_date
                break

            # If we find a suitable date before the due date, use it and continue
            # looking for better options until we hit the due date
            if in_date < entry.due_date and expense_amount <= up_to:
                income_date = in_date
                # Continue to potentially find a better (closer to due date) option

            # Once we reach or pass the due date, stop looking
            if in_date >= entry.due_date:
                break

        return income_date

    def schedule_expense_entries_pass(self, schedule_entries):
        unscheduled = []
        for entry in schedule_entries:
            income_date = self.schedule_expense_entry(entry)
            if income_date is not None:
                # Set the income_date on the entry so it's saved to the database
                entry.income_date = income_date
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

        # Paid items are preserved at the database level (clear_unpaid_extrapolation_items)
        # so the scheduler only operates on unpaid entries
        unscheduled = self.schedule_expense_entries_pass(
            self.unscheduled_schedule_entries
        )

        # push up unscheduled to find spots if possible
        self.push_expenses_up = True
        unscheduled = self.schedule_expense_entries_pass(unscheduled)

        # // admit to our losses? should check if needed I guess
        self.schedule.unscheduled_entries = unscheduled

    def compute_savings(self):
        """
        Compute savings opportunities by analyzing schedule surplus.
        Returns a list of ExtrapolationItem objects representing potential savings.
        """
        from database.extrapolation_item import ExtrapolationItem
        from datetime import timedelta
        
        savings_items = []
        
        # Build the schedule first if not already built
        if not self.schedule or not self.schedule.columns:
            if not self.start_date or not self.end_date:
                self.start_date = date.today()
                self.end_date = date.today() + timedelta(days=365)
            
            self.schedule = Schedule()
            self.build_input_date_columns()
            self.build_unscheduled_schedule_entries()
            self.schedule_expense_entries_pass(self.unscheduled_schedule_entries)
        
        # Analyze each income date for surplus
        for income_date in self.schedule.sorted_income_dates:
            date_key = income_date.strftime("%Y-%m-%d")
            if date_key in self.schedule.columns:
                column = self.schedule.columns[date_key]
                
                # Calculate total for this column
                income_total = sum(entry.amount for entry in column.incomes)
                expense_total = sum(abs(entry.amount) for entry in column.expenses)
                surplus = income_total - expense_total
                
                # If there's a surplus, it could be saved
                if surplus > 0:
                    savings_item = ExtrapolationItem(
                        due_date=income_date,
                        amount=surplus,
                        income_date=income_date,
                        budget_item_id=None
                    )
                    savings_items.append(savings_item)
        
        return savings_items
