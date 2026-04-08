import operator
from datetime import date, datetime
import os
import odswriter as odswriter

from shedule.schedule import Schedule


class ScheduleWriter:
    schedule: Schedule

    def __init__(self, schedule: Schedule) -> None:
        self.schedule = schedule

    def col_letter(self, num: int) -> str:
        """Convert 1-based column index to spreadsheet letter (1=A, 27=AA, etc.)."""
        letters = ""
        while num:
            mod = (num - 1) % 26
            letters += chr(mod + 65)
            num = (num - 1) // 26
        return "".join(reversed(letters))

    def write_spreadsheet(self, output_dir: str = "schedule-spreadsheets", max_backups: int = 5000):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        datetimestr = datetime.now().strftime("%Y-%m-%d:%H-%M-%S:%f")
        filename = f"schedule.{self.schedule.profile_id}.{datetimestr}.ods"
        filepath = os.path.join(output_dir, filename)

        income_items = self.schedule.income_budget_items
        expense_items = self.schedule.expense_budget_items
        dates = self.schedule.sorted_income_dates
        columns = self.schedule.columns

        # ── Row layout (1-based for formulas) ──
        # Row 1: Date headers
        # Row 2: Column sub-headers (Scheduled / Actual / Variance / Status)
        # Row 3: Carryover
        # Row 4..4+len(income)-1: Income items
        # next: Income Total
        # next..+len(expense)-1: Expense items
        # next: Expenses Total
        # next: Leftover (Income - Expenses)
        # next: Safe to Spend (Carryover + Income - Expenses)

        r_carryover = 3
        r_income_start = 4
        r_income_end = r_income_start + len(income_items) - 1
        r_income_total = r_income_end + 1
        r_expense_start = r_income_total + 1
        r_expense_end = r_expense_start + len(expense_items) - 1
        r_expense_total = r_expense_end + 1
        r_leftover = r_expense_total + 1
        r_safe_to_spend = r_leftover + 1

        # Each income_date gets 4 columns: Scheduled, Actual, Variance, Status
        # Column A (1) = item names
        cols_per_date = 4

        def sched_col(date_idx):
            """Scheduled column letter for a given date index (0-based)."""
            return self.col_letter(2 + date_idx * cols_per_date)

        def actual_col(date_idx):
            return self.col_letter(3 + date_idx * cols_per_date)

        def variance_col(date_idx):
            return self.col_letter(4 + date_idx * cols_per_date)

        def status_col(date_idx):
            return self.col_letter(5 + date_idx * cols_per_date)

        # ── Build header rows ──
        date_header = [""]
        sub_header = ["Item"]
        for d in dates:
            date_header.extend([d.strftime("%Y-%m-%d"), "", "", ""])
            sub_header.extend(["Scheduled", "Actual", "Variance", "Status"])

        # ── Build carryover row ──
        carryover_row = ["Carryover"]
        for di, d in enumerate(dates):
            date_str = d.strftime("%Y-%m-%d")
            col = columns.get(date_str)
            sc = sched_col(di)
            ac = actual_col(di)
            vc = variance_col(di)

            if di == 0:
                # First column: static starting balance
                balance = col.starting_balance if col else 0
                carryover_row.append(balance)
                carryover_row.append(balance)
            else:
                # Reference previous column's Safe to Spend
                prev_sc = sched_col(di - 1)
                prev_ac = actual_col(di - 1)
                carryover_row.append(odswriter.Formula(f"={prev_sc}{r_safe_to_spend}"))
                carryover_row.append(odswriter.Formula(f"={prev_ac}{r_safe_to_spend}"))
            # Variance = Actual - Scheduled
            carryover_row.append(odswriter.Formula(f"={ac}{r_carryover}-{sc}{r_carryover}"))
            carryover_row.append("")  # No status for carryover

        # ── Build income rows ──
        income_rows = []
        for item in income_items:
            row = [item.name]
            for di, d in enumerate(dates):
                date_str = d.strftime("%Y-%m-%d")
                col = columns.get(date_str)
                entry = None
                if col:
                    entry = next((e for e in col.incomes if e.budget_item.id == item.id), None)

                if entry is not None:
                    scheduled_amt = entry.scheduled()
                    actual_amt = entry.total()
                    status = "Paid" if entry.all_paid() else ("Partial" if entry.total_paid() > 0 else "Unpaid")
                    sc = sched_col(di)
                    ac = actual_col(di)
                    r = r_income_start + len(income_rows)
                    row.append(scheduled_amt)
                    row.append(actual_amt)
                    row.append(odswriter.Formula(f"={ac}{r}-{sc}{r}"))
                    row.append(status)
                else:
                    row.append(0)
                    row.append(0)
                    row.append(0)
                    row.append("")
            income_rows.append(row)

        # ── Income Total row (SUM of all income items) ──
        income_total_row = ["Income Total"]
        for di in range(len(dates)):
            sc = sched_col(di)
            ac = actual_col(di)
            vc = variance_col(di)
            income_total_row.append(odswriter.Formula(
                f"=SUM({sc}{r_income_start}:{sc}{r_income_end})"
            ))
            income_total_row.append(odswriter.Formula(
                f"=SUM({ac}{r_income_start}:{ac}{r_income_end})"
            ))
            income_total_row.append(odswriter.Formula(
                f"=SUM({vc}{r_income_start}:{vc}{r_income_end})"
            ))
            income_total_row.append("")

        # ── Build expense rows ──
        expense_rows = []
        for item in expense_items:
            row = [item.name]
            for di, d in enumerate(dates):
                date_str = d.strftime("%Y-%m-%d")
                col = columns.get(date_str)
                entry = None
                if col:
                    entry = next((e for e in col.expenses if e.budget_item.id == item.id), None)

                if entry is not None:
                    scheduled_amt = entry.scheduled()
                    actual_amt = entry.total()
                    status = "Paid" if entry.all_paid() else ("Partial" if entry.total_paid() > 0 else "Unpaid")
                    sc = sched_col(di)
                    ac = actual_col(di)
                    r = r_expense_start + len(expense_rows)
                    row.append(scheduled_amt)
                    row.append(actual_amt)
                    row.append(odswriter.Formula(f"={ac}{r}-{sc}{r}"))
                    row.append(status)
                else:
                    row.append(0)
                    row.append(0)
                    row.append(0)
                    row.append("")
            expense_rows.append(row)

        # ── Expenses Total row ──
        expense_total_row = ["Expenses Total"]
        for di in range(len(dates)):
            sc = sched_col(di)
            ac = actual_col(di)
            vc = variance_col(di)
            expense_total_row.append(odswriter.Formula(
                f"=SUM({sc}{r_expense_start}:{sc}{r_expense_end})"
            ))
            expense_total_row.append(odswriter.Formula(
                f"=SUM({ac}{r_expense_start}:{ac}{r_expense_end})"
            ))
            expense_total_row.append(odswriter.Formula(
                f"=SUM({vc}{r_expense_start}:{vc}{r_expense_end})"
            ))
            expense_total_row.append("")

        # ── Leftover row (Income Total + Expenses Total; expenses are negative) ──
        leftover_row = ["Leftover"]
        for di in range(len(dates)):
            sc = sched_col(di)
            ac = actual_col(di)
            vc = variance_col(di)
            leftover_row.append(odswriter.Formula(
                f"={sc}{r_income_total}+{sc}{r_expense_total}"
            ))
            leftover_row.append(odswriter.Formula(
                f"={ac}{r_income_total}+{ac}{r_expense_total}"
            ))
            leftover_row.append(odswriter.Formula(
                f"={vc}{r_income_total}+{vc}{r_expense_total}"
            ))
            leftover_row.append("")

        # ── Safe to Spend row (Carryover + Income + Expenses) ──
        safe_to_spend_row = ["Safe to Spend"]
        for di in range(len(dates)):
            sc = sched_col(di)
            ac = actual_col(di)
            vc = variance_col(di)
            safe_to_spend_row.append(odswriter.Formula(
                f"={sc}{r_carryover}+{sc}{r_leftover}"
            ))
            safe_to_spend_row.append(odswriter.Formula(
                f"={ac}{r_carryover}+{ac}{r_leftover}"
            ))
            safe_to_spend_row.append(odswriter.Formula(
                f"={vc}{r_carryover}+{vc}{r_leftover}"
            ))
            safe_to_spend_row.append("")

        # ── Write the schedule sheet ──
        with odswriter.writer(open(filepath, "wb")) as odsfile:
            odsfile.writerow(date_header)
            odsfile.writerow(sub_header)
            odsfile.writerow(carryover_row)
            for row in income_rows:
                odsfile.writerow(row)
            odsfile.writerow(income_total_row)
            for row in expense_rows:
                odsfile.writerow(row)
            odsfile.writerow(expense_total_row)
            odsfile.writerow(leftover_row)
            odsfile.writerow(safe_to_spend_row)

            # ── Library sheets (raw data for reference) ──
            self._write_library(odsfile)

        # Enforce backup retention
        import glob as glob_module
        pattern = os.path.join(output_dir, f"schedule.{self.schedule.profile_id}.*.ods")
        existing = sorted(glob_module.glob(pattern), key=os.path.getmtime)
        while len(existing) > max_backups:
            os.remove(existing.pop(0))

    def _write_library(self, odsfile):
        """Write raw data sheets for accounts, ledger, budget items, and extrapolation items."""
        # Accounts sheet
        accounts_sheet = odsfile.new_sheet("Accounts")
        accounts_sheet.writerow(["ID", "Name", "Type", "Profile ID", "Created", "Updated"])
        for acc in self.schedule.accounts:
            accounts_sheet.writerow([
                acc.id, acc.name, acc.account_type,
                self.schedule.profile_id, acc.created_at, acc.updated_at,
            ])

        # Ledger sheet
        ledger_sheet = odsfile.new_sheet("Ledger")
        ledger_sheet.writerow(["ID", "Account ID", "Name", "Paid Date", "Income Date", "Amount", "Type", "Created", "Updated"])
        for acc in self.schedule.accounts:
            for le in self.schedule.ledger_entries_by_account.get(acc.id, []):
                ledger_sheet.writerow([
                    le.id, le.account_id, le.name, le.paid_date,
                    le.income_date, le.amount, le.type, le.created_at, le.updated_at,
                ])

        # Budget Items sheet
        budget_sheet = odsfile.new_sheet("Budget Items")
        budget_sheet.writerow(["ID", "Name", "Type", "Amount", "Start Date", "End Date", "Group ID", "Periods"])
        for bi in self.schedule.budget_item_list:
            periods_str = "; ".join(
                f"{p.type}={p.value}" + (f" (biz day {p.business_day})" if p.business_day else "")
                for p in bi.periods
            )
            budget_sheet.writerow([
                bi.id, bi.name, bi.type, bi.amount,
                bi.start_date, bi.end_date, bi.budget_group_id, periods_str,
            ])

        # Extrapolation Items sheet
        extrap_sheet = odsfile.new_sheet("Extrapolation Items")
        extrap_sheet.writerow(["ID", "Due Date", "Amount", "Income Date", "Budget Item ID", "Ledger Entry ID", "Category", "Name"])
        for ei in self.schedule.extrapolation_items:
            extrap_sheet.writerow([
                ei.id, ei.due_date, ei.amount, ei.income_date,
                ei.budget_item_id, ei.ledger_entry_id, ei.category, ei.name,
            ])
