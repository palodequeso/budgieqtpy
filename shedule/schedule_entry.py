from datetime import date

from database.budget_item import BudgetItem
from shedule.schedule_entry_item import ScheduleEntryItem


class ScheduleEntry:
    budget_item: BudgetItem = None
    income_date: date = None
    type: str = None
    items: list[ScheduleEntryItem] = []

    def __init__(
        self,
        type: str = None,
        income_date: date = None,
        budget_item: BudgetItem = None,
        items: list[ScheduleEntryItem] = [],
    ):
        self.type = type
        self.income_date = income_date
        self.budget_item = budget_item
        self.items = items

    def add_item(self, item: ScheduleEntryItem):
        self.items.append(item)

    def all_paid(self) -> bool:
        for item in self.items:
            if item.ledger_entry is None:
                return False
        return True

    def scheduled(self) -> float:
        total = 0
        for item in self.items:
            total += float(item.extrapolation_item.amount)
        return total

    def total(self) -> float:
        total = 0
        for item in self.items:
            if item.ledger_entry is not None:
                total += float(item.ledger_entry.amount)
            else:
                total += float(item.extrapolation_item.amount)
        return total

    def total_paid(self) -> float:
        total = 0
        for item in self.items:
            if item.ledger_entry is not None:
                total += float(item.ledger_entry.amount)
        return total
