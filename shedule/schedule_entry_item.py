from database.budget_item import BudgetItem
from database.extrapolation_item import ExtrapolationItem
from database.ledger_entry import LedgerEntry


class ScheduleEntryItem:
    extrapolation_item: ExtrapolationItem = None
    ledger_entry: LedgerEntry = None

    def __init__(
        self, extrapolation_item: ExtrapolationItem, ledger_entry: LedgerEntry = None
    ):
        self.extrapolation_item = extrapolation_item
        self.ledger_entry = ledger_entry
