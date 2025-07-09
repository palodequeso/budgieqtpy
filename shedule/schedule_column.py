from datetime import date

from shedule.schedule_entry import ScheduleEntry


class ScheduleColumn:
    income_date: date = None
    starting_balance: float = 0
    incomes: list[ScheduleEntry] = []
    expenses: list[ScheduleEntry] = []

    def __init__(self, income_date: date = None, starting_balance: float = 0):
        self.income_date = income_date
        self.starting_balance = starting_balance
        self.incomes = []
        self.expenses = []

    def add_income(self, item: ScheduleEntry):
        self.incomes.append(item)

    def add_expense(self, entry: ScheduleEntry):
        self.expenses.append(entry)

    # def __repr__(self):
        # return f"Column: {self.income_date.strftime('%Y-%m-%d')} - {self.total()} {len(self.incomes)} {len(self.expenses)}"

    def income_total(self):
        total = 0
        for income in self.incomes:
            total += float(income.total())
        return total

    def expenses_total(self):
        total = 0
        for expense in self.expenses:
            total += float(expense.total())
        return total

    def total(self):
        total = (
            float(self.starting_balance) + self.income_total() + self.expenses_total()
        )
        # print(
        #     "ScheduleColumn::total()",
        #     self.income_date,
        #     self.starting_balance,
        #     self.income_total(),
        #     self.expenses_total(),
        #     total,
        # )
        return total
