import operator
from datetime import date, datetime
import os
import odswriter as odswriter

from shedule.schedule import Schedule


class ScheduleWriter:
    schedule: Schedule

    def __init__(self, schedule: Schedule) -> None:
        self.schedule = schedule

    def column_index_to_letter(self, num: int) -> str:
        letters = ""
        while num:
            mod = (num - 1) % 26
            letters += chr(mod + 65)
            num = (num - 1) // 26
        return "".join(reversed(letters))

    def build_row_numbers(self) -> dict:
        row_numbers = {
            "Carryover": 2,
        }
        current_row_number = 3
        for income_budget_item in self.schedule.income_budget_items:
            row_numbers[income_budget_item.name] = current_row_number
            current_row_number += 1
        for expense_budget_item in self.schedule.expense_budget_items:
            row_numbers[expense_budget_item.name] = current_row_number
            current_row_number += 1
        row_numbers["Subtotal"] = current_row_number
        current_row_number += 1
        row_numbers["Total"] = current_row_number

        return row_numbers

    def build_column_letters(self) -> tuple:
        column_letters = {}
        item_header_row = ["Item"]
        date_header_row = ["Date"]
        current_column_number = 1
        for date in self.schedule.sorted_income_dates:
            date_key = date.strftime("%Y-%m-%d")
            column_letters[date_key] = {
                "scheduled": self.column_index_to_letter(current_column_number),
                "actual": self.column_index_to_letter(current_column_number + 1),
                "status": self.column_index_to_letter(current_column_number + 2),
            }

            date_header_row.append(date_key)
            date_header_row.append("")
            date_header_row.append("")

            item_header_row.append("scheduled")
            item_header_row.append("actual")
            item_header_row.append("status")
            current_column_number += 3
        return (column_letters, date_header_row, item_header_row)

    def build_carryover_row(self) -> list:
        carryover_row = ["Carryover"]
        # row = ["Carryover"]
        column_index = 2
        for date in self.schedule.sorted_income_dates:
            date_str = date.strftime("%Y-%m-%d")
            column = self.schedule.columns.get(date_str, None)
            if column is not None:
                if column_index == 2:
                    carryover_row.append(column.starting_balance)
                    carryover_row.append(column.starting_balance)
                    carryover_row.append("")
                else:
                    previous_column_letter = self.column_index_to_letter(
                        column_index - 3
                    )
                    previous_actual_column_letter = self.column_index_to_letter(
                        column_index - 2
                    )
                    carryover_row.append(
                        odswriter.Formula(
                            f"={previous_column_letter}{len(self.schedule.expense_budget_items) + 5}"
                        )
                    )
                    carryover_row.append(
                        odswriter.Formula(
                            f"={previous_actual_column_letter}{len(self.schedule.expense_budget_items) + 5}"
                        )
                    )
                    carryover_row.append("")
            else:
                carryover_row.append(None)
                carryover_row.append(None)
                carryover_row.append(None)
            column_index += 3
        return carryover_row

    def build_income_row(self, income_budget_item) -> list:
        row = [income_budget_item.name]
        for date in self.schedule.sorted_income_dates:
            date_str = date.strftime("%Y-%m-%d")
            column = self.schedule.columns.get(date_str, None)
            if column is not None:
                entry = next(
                    (
                        e
                        for e in column.incomes
                        if e.budget_item.id == income_budget_item.id
                    ),
                    None,
                )
                if entry is not None:
                    status = "Unpaid"
                    if entry.all_paid():
                        status = "Paid"
                    elif entry.total_paid() > 0:
                        status = "Some"
                    row.append(entry.scheduled())
                    row.append(entry.total())
                    row.append(status)
                else:
                    row.append(None)
                    row.append(None)
                    row.append(None)
            else:
                row.append(None)
                row.append(None)
                row.append(None)
            return row

    def build_expense_row(self, expense_budget_item) -> list:
        row = [expense_budget_item.name]
        for date in self.schedule.sorted_income_dates:
            date_str = date.strftime("%Y-%m-%d")
            column = self.schedule.columns.get(date_str, None)
            if column is not None:
                entry = next(
                    (
                        e
                        for e in column.expenses
                        if e.budget_item.id == expense_budget_item.id
                    ),
                    None,
                )
                if entry is not None:
                    status = "Unpaid"
                    if entry.all_paid():
                        status = "Paid"
                    elif entry.total_paid() > 0:
                        status = "Some"
                    row.append(entry.scheduled())
                    row.append(entry.total())
                    row.append(status)
                else:
                    row.append(None)
                    row.append(None)
                    row.append(None)
            else:
                row.append(None)
                row.append(None)
                row.append(None)
        return row

    def build_subtotal_row(
        self, carryover_row_number, income_count, subtotal_row_number
    ) -> list:
        row = ["Subtotal"]
        column_index = 2
        for date in self.schedule.sorted_income_dates:
            date_str = date.strftime("%Y-%m-%d")
            column = self.schedule.columns.get(date_str, None)
            if column is not None:
                column_letter = self.column_index_to_letter(column_index)
                row.append(
                    odswriter.Formula(
                        f"SUM({column_letter}{carryover_row_number + income_count + 2}:{column_letter}{subtotal_row_number})"
                    )
                )
                row.append(
                    odswriter.Formula(
                        f"SUM({column_letter}{carryover_row_number + income_count + 2}:{column_letter}{subtotal_row_number})"
                    )
                )
                row.append("")
            else:
                row.append(None)
                row.append(None)
                row.append(None)
            column_index += 3
        return row

    def build_total_row(
        self, carryover_row_number, income_count, subtotal_row_number
    ) -> list:
        row = ["Total"]
        column_index = 2
        for date in self.schedule.sorted_income_dates:
            date_str = date.strftime("%Y-%m-%d")
            column = self.schedule.columns.get(date_str, None)
            if column is not None:
                column_letter = self.column_index_to_letter(column_index)
                formula_str = f"=SUM({column_letter}{carryover_row_number + 2} + {column_letter}{subtotal_row_number + 1}"
                for i in range(income_count):
                    formula_str += f" + {column_letter}{carryover_row_number + i + 1}"
                formula_str += ")"
                row.append(odswriter.Formula(formula_str))
                row.append(odswriter.Formula(formula_str))
                row.append("")
            else:
                row.append(None)
                row.append(None)
                row.append(None)
            column_index += 3
        return row

    def write_library(self, odsfile):
        # profiles_sheet = odsfile.new_sheet("Profiles")
        # profiles_sheet.writerow(["id", "name", "created_at", "updated_at"])
        # profiles = 

        accounts_sheet = odsfile.new_sheet("Accounts")
        accounts_sheet.writerow(["id", "name", "type", "profile_id", "created_at", "updated_at"])
        for account in self.schedule.accounts:
            accounts_sheet.writerow(
                [
                    account.id,
                    account.name,
                    account.account_type,
                    self.schedule.profile_id,
                    account.created_at,
                    account.updated_at,
                ]
            )

        ledger_sheet = odsfile.new_sheet("Ledger")
        ledger_sheet.writerow(
            [
                "id",
                "account_id",
                "paid_date",
                "income_date",
                "amount",
                "type",
                "created_at",
                "updated_at",
            ]
        )
        for account in self.schedule.accounts:
            for ledger_entry in self.schedule.ledger_entries_by_account[account.id]:
                ledger_sheet.writerow(
                    [
                        ledger_entry.id,
                        ledger_entry.account_id,
                        ledger_entry.paid_date,
                        ledger_entry.income_date,
                        ledger_entry.amount,
                        ledger_entry.type,
                        ledger_entry.created_at,
                        ledger_entry.updated_at,
                    ]
                )

        budget_sheet = odsfile.new_sheet("Budget")
        budget_sheet.writerow(["id", "profile_id", "name", "type", "created_at", "updated_at"])
        for budget_item in self.schedule.budget_item_list:
            budget_sheet.writerow(
                [
                    budget_item.id,
                    self.schedule.profile_id,
                    budget_item.name,
                    budget_item.type,
                    budget_item.created_at,
                    budget_item.updated_at,
                ]
            )
            for period in budget_item.periods:
                budget_sheet.writerow(
                    [
                        '',
                        period.id,
                        budget_item.id,
                        period.type,
                        period.value,
                        period.business_day,
                        period.created_at,
                        period.updated_at,
                    ]
                )

        extrapolation_sheet = odsfile.new_sheet("ExtrapolationItems")
        extrapolation_sheet.writerow(["id", "due_date", "amount", "income_date", "created_at", "updated_at", "budget_item_id", "ledger_entry_id"])
        for extrapolation_item in self.schedule.extrapolation_items:
            extrapolation_sheet.writerow(
                [
                    extrapolation_item.id,
                    extrapolation_item.due_date,
                    extrapolation_item.amount,
                    extrapolation_item.income_date,
                    extrapolation_item.created_at,
                    extrapolation_item.updated_at,
                    extrapolation_item.budget_item_id,
                    extrapolation_item.ledger_entry_id
                ]
            )


    def write_spreadsheet(self):
        # ensure folder exists
        # TODO: Make this path configurable
        # NOTE: This is supposed to be making backups in physical spreadsheet form.
        # TODO: Only keep last X thousand of them, a thousand should be like 100MB
        if not os.path.exists("schedule-spreadsheets"):
            os.makedirs("schedule-spreadsheets")
        datetimestr = datetime.now().strftime("%Y-%m-%d:%H-%M-%S:%f")
        filename = f"schedule.{self.schedule.profile_id}.{datetimestr}.ods"
        filepath = os.path.join("schedule-spreadsheets", filename)

        row_numbers = self.build_row_numbers()
        (column_letters, date_header_row, item_header_row) = self.build_column_letters()

        with odswriter.writer(open(filepath, "wb")) as odsfile:
            odsfile.writerow(date_header_row)
            odsfile.writerow(item_header_row)
            odsfile.writerow(self.build_carryover_row())
            for income_budget_item in self.schedule.income_budget_items:
                odsfile.writerow(self.build_income_row(income_budget_item))
            for expense_budget_item in self.schedule.expense_budget_items:
                odsfile.writerow(self.build_expense_row(expense_budget_item))
            odsfile.writerow(
                self.build_subtotal_row(
                    row_numbers["Carryover"],
                    len(self.schedule.income_budget_items),
                    row_numbers["Subtotal"],
                )
            )
            odsfile.writerow(
                self.build_total_row(
                    row_numbers["Carryover"],
                    len(self.schedule.income_budget_items),
                    row_numbers["Subtotal"],
                )
            )
            self.write_library(odsfile)
