import operator
from datetime import date, datetime
import os
import odswriter as odswriter

from database.account import Account
from database.budget_item import BudgetItem
from database.database import Database
from database.extrapolation_item import ExtrapolationItem
from database.ledger_entry import LedgerEntry
from shedule.schedule_entry import ScheduleEntry
from shedule.schedule_entry_item import ScheduleEntryItem
from .schedule_column import ScheduleColumn


class Schedule:
    start_date: date = None
    end_date: date = None
    profile_id: int = None
    columns: dict[str, ScheduleColumn] = {}
    expense_budget_items: list[BudgetItem] = []
    income_budget_items: list[BudgetItem] = []
    starting_balance: float = 0
    sorted_income_dates: list[date] = []
    budget_item_list: list[BudgetItem] = []
    budget_items: dict[int, BudgetItem] = []
    extrapolation_items: list[ExtrapolationItem] = []
    accounts: list[Account] = []
    ledger_entries_by_account: dict[int, list[LedgerEntry]] = {}
    ledger_entries_by_id: dict[int, LedgerEntry] = {}
    unscheduled_entries: list[ScheduleEntry] = []
    # self.one_offs = []

    def __init__(self):
        self.clear()

    def clear(self):
        self.profile_id = None
        self.start_date = None
        self.end_date = None
        self.columns = {}
        self.starting_balance = 0
        self.sorted_income_dates = []
        self.expense_budget_items = []
        self.income_budget_items = []
        self.unscheduled_entries = []
        self.accounts = []
        self.budget_item_list = []
        self.extrapolation_items = []
        self.ledger_entries_by_account = {}
        self.ledger_entries_by_id = {}
        self.budget_items = {}

    def fetch_schedule(self, database: Database, profile_id):
        self.clear()

        self.profile_id = profile_id

        # fetch some data
        self.budget_item_list = database.fetch_budget_items(profile_id)
        self.accounts = database.fetch_accounts(profile_id)
        self.extrapolation_items: list[ExtrapolationItem] = sorted(
            database.fetch_extrapolation_items(profile_id),
            key=operator.attrgetter("income_date"),
            reverse=True,
        )

        # Create a dictionary of budget items
        for budget_item in self.budget_item_list:
            self.budget_items[budget_item.id] = budget_item
            if budget_item.type == "Income":
                self.income_budget_items.append(budget_item)
            else:
                self.expense_budget_items.append(budget_item)

        # Create a dictionary of ledger entries and list by account
        for account in self.accounts:
            self.ledger_entries_by_account[account.id] = sorted(
                database.fetch_ledger_items(account.id),
                key=operator.attrgetter("paid_date"),
                reverse=True,
            )
            for ledger_entry in self.ledger_entries_by_account[account.id]:
                self.ledger_entries_by_id[ledger_entry.id] = ledger_entry

    def build_schedule(self):
        # Create the schedule
        for item in self.extrapolation_items:
            date_key = item.income_date.strftime("%Y-%m-%d")
            if self.columns.get(date_key, None) is None:
                self.columns[date_key] = ScheduleColumn(item.income_date, 0)

            # find associated budget item
            budget_item = self.budget_items.get(item.budget_item_id, None)
            if budget_item is None:
                print(f"budget item {item.budget_item_id} not found")
                continue

            schedule_entry: ScheduleEntry = None
            if budget_item.type == "Income":
                schedule_entry = next((e for e in self.columns[date_key].incomes if e.budget_item.id == budget_item.id), None)
            else:
                schedule_entry = next((e for e in self.columns[date_key].expenses if e.budget_item.id == budget_item.id), None)
            if schedule_entry is None:
                schedule_entry = ScheduleEntry(
                    budget_item.type, item.income_date, budget_item, []
                )
                if budget_item.type == "Expense":
                    self.columns[date_key].add_expense(schedule_entry)
                else:
                    self.columns[date_key].add_income(schedule_entry)  # TODO: Handle multiple incomes

            entry_item = ScheduleEntryItem(item)
            if item.ledger_entry_id is not None:
                entry_item.ledger_entry = self.ledger_entries_by_id.get(item.ledger_entry_id, None)
            schedule_entry.add_item(entry_item)

        column_keys = list(self.columns.keys())
        column_keys = [date.fromisoformat(x) for x in column_keys]
        self.sorted_income_dates = sorted(column_keys)

        # compute starting balances for columns (bring over)
        previous_income_date = None
        for income_date in self.sorted_income_dates:
            column = self.columns.get(income_date.strftime("%Y-%m-%d"), None)
            if column is None:
                print(f"column {income_date.strftime('%Y-%m-%d')} not found")
                continue

            starting_balance = 0
            if previous_income_date is None:
                # add up ledgers before income date
                for entry in self.ledger_entries_by_id.values():
                    if entry.paid_date.date() < income_date:
                        starting_balance += entry.amount
            else:
                # use the previous column total
                previous_column = self.columns.get(
                    previous_income_date.strftime("%Y-%m-%d"), None
                )
                if previous_column is None:
                    print(f"previous column {previous_income_date.strftime('%Y-%m-%d')} not found")
                    continue
                starting_balance = previous_column.total()
            # TODO: This is kinda hard, need to consider previous column total, and their ledger_item/extrapolation_item balance
            column.starting_balance = starting_balance
            previous_income_date = income_date

    def get_total_as_of(self, in_date: date, inclusive=True):
        # find closest income date
        closest_income_date = next(
            d
            for d in self.sorted_income_dates
            if (d <= in_date if inclusive else d < in_date)
        )

        # if no income date, return starting balance
        if not closest_income_date:
            return self.starting_balance

        # get total as of closest income date
        total = float(self.starting_balance)
        for income_date in self.sorted_income_dates:
            if income_date <= in_date if inclusive else income_date < in_date:
                date_str = income_date.strftime("%Y-%m-%d")
                if self.columns.get(date_str, None) is not None:
                    total += float(self.columns[date_str].total())
            else:
                break

        return total
