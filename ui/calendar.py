import locale
from datetime import date, datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QDateEdit,
    QLabel,
    QDialog,
    QComboBox,
    QHeaderView,
    QLineEdit,
    QCheckBox,
)
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtCore import pyqtSlot as Slot
from database.database import Database
from database.extrapolation_item import ExtrapolationItem
from database.profile import Profile
from scheduler.default_knapsack import DefaultKnapsack
from shedule.schedule import Schedule
from shedule.schedule_entry import ScheduleEntry
from shedule.schedule_entry_item import ScheduleEntryItem
from shedule.schedule_writer import ScheduleWriter

locale.setlocale(locale.LC_ALL, "C")

MONTH_COLORS = [
    QColor("#B71C1C"),
    QColor("#880E4F"),
    QColor("#4A148C"),
    QColor("#827717"),
    QColor("#E65100"),
    QColor("#0D47A1"),
    QColor("#01579B"),
    QColor("#006064"),
    QColor("#004D40"),
    QColor("#1B5E20"),
    QColor("#33691E"),
    QColor("#827717"),
    QColor("#263238"),
    # alt colors
    QColor("#D32F2F"),
    QColor("#C2185B"),
    QColor("#7B1FA2"),
    QColor("#AFB42B"),
    QColor("#F57C00"),
    QColor("#1976D2"),
    QColor("#0288D1"),
    QColor("#0097A7"),
    QColor("#00796B"),
    QColor("#388E3C"),
    QColor("#689F38"),
    QColor("#AFB42B"),
    QColor("#455A64"),
]


class Calendar(QWidget):
    db: Database = None
    selected_profile: Profile = None
    schedule: Schedule = None
    grid_entries: dict[int, ScheduleEntry] = None
    entry_widget: QWidget = None
    schedule_widget: QWidget = None
    schedule_writer: ScheduleWriter = None

    def __init__(self, db, selected_profile):
        super().__init__()
        self.db = db
        self.selected_profile = selected_profile
        self.schedule = Schedule()
        self.schedule.fetch_schedule(self.db, self.selected_profile.id)
        self.schedule.build_schedule()
        # self.schedule.write_spreadsheet()
        self.schedule_writer = ScheduleWriter(self.schedule)
        self.schedule_writer.write_spreadsheet()
        self.grid_entries = {}
        self.entry_widget = None
        self.schedule_widget = None

        self.schedule_vertical_layout = QVBoxLayout()

        toolsRow = QHBoxLayout()
        toolsRow.addStretch(1)

        hide_current_column_button = QPushButton("Hide Current Column")
        hide_current_column_button.setStyleSheet("background-color: rgb(0, 0, 64);")
        toolsRow.addWidget(hide_current_column_button)
        hide_current_column_button.clicked.connect(self.hide_current_column)

        got_paid_button = QPushButton("I Got Paid")
        # make it green!
        # got_paid_button.setBackgroundRole(QColor(0, 192, 0))
        got_paid_button.setStyleSheet("background-color: rgb(0, 64, 0);")
        toolsRow.addWidget(got_paid_button)
        got_paid_button.clicked.connect(self.got_paid)

        add_one_off_button = QPushButton("Add One Off")
        toolsRow.addWidget(add_one_off_button)
        add_one_off_button.clicked.connect(self.add_one_off_entry)

        add_savings_items_button = QPushButton("Add Savings Items")
        toolsRow.addWidget(add_savings_items_button)
        add_savings_items_button.clicked.connect(self.set_savings_items)
        # add_savings_items_button.setEnabled(False)

        fix_unscheduled_button = QPushButton("Fix Unscheduled")
        toolsRow.addWidget(fix_unscheduled_button)
        fix_unscheduled_button.clicked.connect(self.fix_unscheduled)
        fix_unscheduled_button.setEnabled(False)

        start_date_label = QLabel("Start Date")
        toolsRow.addWidget(start_date_label)

        extraplatilon_start_date = QDateEdit()
        extraplatilon_start_date.setDate(date.today())
        extraplatilon_start_date.setCalendarPopup(True)
        toolsRow.addWidget(extraplatilon_start_date)

        end_date_label = QLabel("End Date")
        toolsRow.addWidget(end_date_label)

        extraplatilon_end_date = QDateEdit()
        extraplatilon_end_date.setDate(date.today() + timedelta(days=365))
        extraplatilon_end_date.setCalendarPopup(True)
        toolsRow.addWidget(extraplatilon_end_date)

        extrapolate_button = QPushButton("Extrapolate")
        toolsRow.addWidget(extrapolate_button)
        extrapolate_button.clicked.connect(
            lambda: self.extrapolate_budget(self.schedule_vertical_layout)
        )

        self.schedule_vertical_layout.addLayout(toolsRow)

        self.setLayout(self.schedule_vertical_layout)

        self.render_schedule(self.schedule_vertical_layout)

    def date_to_color(self, date, dull=False):
        if dull:
            if date.day >= 15:
                return MONTH_COLORS[25]
            return MONTH_COLORS[12]
        if date.day >= 15:
            return MONTH_COLORS[(date.month - 1) + 13]
        return MONTH_COLORS[date.month - 1]

    def format_currency(self, amount):
        return "${:,.2f}".format(amount)
        # return locale.currency(amount, grouping=True)

    def create_cell(self, date, value: float, bold=False, dull=False, paid=False):
        out_str = ""
        if value is not None:
            out_str = self.format_currency(value)
        item = QTableWidgetItem(out_str)
        item.setBackground(QBrush(self.date_to_color(date, dull)))
        if bold:
            f = QFont()
            f.setBold(True)
            item.setFont(f)
        if paid:
            f = QFont()
            f.setStrikeOut(True)
            item.setFont(f)
        return item

    def hide_current_column(self):
        current_column_income_date = self.schedule.sorted_income_dates[0]
        print("TODO: hide current column", current_column_income_date)
        hide_current_column_dialog = QDialog()

        hide_current_column_layout = QVBoxLayout()
        hide_current_column_layout.addWidget(
            QLabel(
                "Current Income Date: "
                + current_column_income_date.strftime("%Y-%m-%d")
            )
        )

        hide_current_column_ending_balance = QLineEdit()
        hide_current_column_ending_balance.setText(
            str(
                self.schedule.columns[
                    current_column_income_date.strftime("%Y-%m-%d")
                ].total()
            )
        )
        hide_current_column_layout.addWidget(QLabel("Ending Balance: "))
        hide_current_column_layout.addWidget(hide_current_column_ending_balance)

        hide_current_column_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        hide_current_column_cancel_button = QPushButton("Cancel")
        buttons_layout.addWidget(hide_current_column_cancel_button)
        hide_current_column_cancel_button.clicked.connect(
            lambda: hide_current_column_dialog.close()
        )
        hide_current_column_save_button = QPushButton("Save")
        buttons_layout.addWidget(hide_current_column_save_button)
        hide_current_column_save_button.clicked.connect(
            lambda: hide_current_column_dialog.close()
        )
        hide_current_column_layout.addLayout(buttons_layout)

        hide_current_column_dialog.setLayout(hide_current_column_layout)
        hide_current_column_dialog.exec()

    def select_entry(self, entry: ScheduleEntry):
        if self.entry_widget is not None:
            self.layout().removeWidget(self.entry_widget)
            del self.entry_widget

        self.entry_widget = QWidget()
        self.entry_widget.setFixedHeight(100)
        entry_layout = QHBoxLayout()

        entry_layout.addStretch(1)

        summary_layout = QVBoxLayout()
        summary_layout.addWidget(QLabel(entry.budget_item.name))
        summary_layout.addWidget(QLabel(entry.budget_item.type))
        summary_layout.addWidget(
            QLabel("Budget Item Amount: ${:,.2f}".format(entry.budget_item.amount))
        )
        summary_layout.addWidget(
            QLabel("Income Date: " + entry.income_date.strftime("%Y-%m-%d"))
        )
        summary_layout.addWidget(
            QLabel("Entry Total: " + self.format_currency(entry.total()))
        )
        summary_layout.addStretch(1)
        entry_layout.addLayout(summary_layout)

        items_layout = QVBoxLayout()
        items_layout.addWidget(QLabel("Items (" + str(len(entry.items)) + "):"))
        for item in entry.items:
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.addWidget(
                QLabel(item.extrapolation_item.due_date.strftime("%Y-%m-%d"))
            )
            item_layout.addWidget(
                QLabel(
                    "Amount: ${:,.2f}".format(
                        item.ledger_entry.amount
                        if item.ledger_entry is not None
                        else item.extrapolation_item.amount
                    )
                )
            )

            if item.ledger_entry is not None:
                item_layout.addWidget(QLabel("Paid"))
            else:
                mark_paid_button = QPushButton("Pay")
                mark_paid_button.clicked.connect(lambda: self.mark_paid(item, entry))
                item_layout.addWidget(mark_paid_button)
            item_widget.setLayout(item_layout)
            items_layout.addWidget(item_widget)

        items_layout.addStretch(1)
        entry_layout.addLayout(items_layout)

        # item.extrapolation_item
        # item.ledger_entry

        # dates_layout = QVBoxLayout()
        # dates_layout.addWidget(
        #     QLabel("Income Date: " + entry.income_date.strftime("%Y-%m-%d"))
        # )
        # dates_layout.addWidget(
        #     QLabel("Due Date: " + entry.due_date.strftime("%Y-%m-%d"))
        # )
        # dates_layout.addStretch(1)
        # entry_layout.addLayout(dates_layout)

        # tools_layout = QVBoxLayout()
        # mark_paid_button = QPushButton("Mark as Paid")
        # tools_layout.addWidget(mark_paid_button)
        # mark_paid_button.clicked.connect(lambda: self.mark_paid(entry))
        # tools_layout.addStretch(1)
        # entry_layout.addLayout(tools_layout)

        entry_layout.addStretch(1)

        self.entry_widget.setLayout(entry_layout)
        self.entry_widget.show()
        self.layout().addWidget(self.entry_widget)

    def got_paid(self):
        accounts = self.db.fetch_accounts(self.selected_profile.id)

        got_paid_dialog = QDialog()
        got_paid_layout = QVBoxLayout()

        dialog_label = QLabel("Hooray, it's payday!")
        got_paid_layout.addWidget(dialog_label)

        income_date_selector = QComboBox()
        income_date_selector.addItems(
            [x.strftime("%Y-%m-%d") for x in self.schedule.sorted_income_dates]
        )
        got_paid_layout.addWidget(income_date_selector)

        account_selector = QComboBox()
        for account in accounts:
            account_selector.addItem(account.name)
        got_paid_layout.addWidget(account_selector)

        got_paid_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(lambda: got_paid_dialog.close())
        buttons_layout.addWidget(cancel_button)
        save_button = QPushButton("Save")
        save_button.clicked.connect(
            lambda: self.got_paid_save(
                income_date_selector.currentText(),
                account_selector.currentText(),
                accounts,
                got_paid_dialog,
            )
        )
        buttons_layout.addWidget(save_button)
        got_paid_layout.addLayout(buttons_layout)

        got_paid_dialog.setLayout(got_paid_layout)
        got_paid_dialog.exec()

    def got_paid_save(self, income_date, account_name, accounts, modal):
        schedule_column = self.schedule.columns[income_date]
        income_entry = schedule_column.incomes[0]
        accounts = self.db.fetch_accounts(self.selected_profile.id)
        account = next(
            (x for x in accounts if x.name == account_name), None
        )
        self.mark_paid_with_ledger(income_entry, income_entry.items[0], account.id, income_entry.total(), date.today(), modal)

    def mark_paid(self, item: ScheduleEntryItem, entry: ScheduleEntry):
        accounts = self.db.fetch_accounts(self.selected_profile.id)

        mark_paid_dialog = QDialog()
        mark_paid_layout = QVBoxLayout()

        mark_paid_layout.addWidget(QLabel("Name: " + entry.budget_item.name))
        mark_paid_layout.addWidget(QLabel("Type: " + entry.budget_item.type))
        mark_paid_layout.addWidget(
            QLabel("Income Date: " + entry.income_date.strftime("%Y-%m-%d"))
        )
        mark_paid_layout.addWidget(
            QLabel("Due Date: " + item.extrapolation_item.due_date.strftime("%Y-%m-%d"))
        )

        account_combobox = QComboBox()
        for account in accounts:
            account_combobox.addItem(account.name)
        account_layout = QHBoxLayout()
        account_layout.addWidget(QLabel("Which account was the entry paid from:"))
        account_layout.addWidget(account_combobox)
        account_layout.addStretch(1)
        mark_paid_layout.addLayout(account_layout)

        paid_amount_layout = QHBoxLayout()
        paid_amount_layout.addWidget(QLabel("Actual Paid Amount: "))
        paid_amount_widget = QLineEdit()
        paid_amount_widget.setText(str(item.extrapolation_item.amount))
        paid_amount_layout.addWidget(paid_amount_widget)
        paid_amount_layout.addStretch(1)
        mark_paid_layout.addLayout(paid_amount_layout)

        paid_date_layout = QHBoxLayout()
        paid_date_layout.addWidget(QLabel("Actual Paid Date: "))
        paid_date_widget = QDateEdit()
        paid_date_widget.setDate(date.today())
        paid_date_layout.addWidget(paid_date_widget)
        paid_date_layout.addStretch(1)
        mark_paid_layout.addLayout(paid_date_layout)

        mark_paid_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        cancel_button = QPushButton("Cancel")
        buttons_layout.addWidget(cancel_button)
        cancel_button.clicked.connect(lambda: mark_paid_dialog.close())
        ok_button = QPushButton("Save")
        buttons_layout.addWidget(ok_button)
        ok_button.clicked.connect(
            lambda: self.mark_paid_with_ledger(
                entry=entry,
                item=item,
                account_id=accounts[account_combobox.currentIndex()].id,
                paid_amount=float(paid_amount_widget.text()),
                paid_date=paid_date_widget.date().toPyDate(),
                modal=mark_paid_dialog,
            )
        )
        mark_paid_layout.addLayout(buttons_layout)

        mark_paid_dialog.setLayout(mark_paid_layout)
        mark_paid_dialog.exec()

    def mark_paid_with_ledger(
        self,
        entry: ScheduleEntry,
        item: ScheduleEntryItem,
        account_id: int,
        paid_amount: float,
        paid_date: date,
        modal: QDialog,
    ):
        ledger = self.db.create_ledger_entry(
            entry.budget_item.name,
            paid_date,
            entry.income_date,
            entry.budget_item.type,
            paid_amount,
            account_id,
        )
        # Check if entry has multiple items, and if other items are not paid, then set the ledger entry for those items
        if len(entry.items) > 1:
            for item in entry.items:
                if item.ledger_entry is None:
                    self.db.update_extrapolation_item_ledger_id(
                        item.extrapolation_item.id, ledger.id
                    )
        else:
            self.db.update_extrapolation_item_ledger_id(
                item.extrapolation_item.id, ledger.id
            )

        self.schedule.fetch_schedule(self.db, self.selected_profile.id)
        self.schedule.build_schedule()
        self.render_schedule(self.schedule_vertical_layout)

        modal.accept()

    @Slot(QTableWidgetItem)
    def cell_clicked(self, item):
        entry = self.grid_entries.get((item.row(), item.column()), None)
        if entry is None:
            return

        self.select_entry(entry)

    def add_one_off_entry(self):
        one_off_dialog = QDialog()
        one_off_layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name: "))
        name_widget = QLineEdit()
        name_layout.addWidget(name_widget)
        name_layout.addStretch(1)
        one_off_layout.addLayout(name_layout)

        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("Amount: "))
        amount_widget = QLineEdit('0.00')
        amount_layout.addWidget(amount_widget)
        amount_layout.addStretch(1)
        one_off_layout.addLayout(amount_layout)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type: "))
        type_widget = QComboBox()
        type_widget.addItem("Expense")
        type_widget.addItem("Income")
        type_layout.addWidget(type_widget)
        type_layout.addStretch(1)
        one_off_layout.addLayout(type_layout)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Due Date: "))
        date_widget = QDateEdit(date.today())
        date_widget.setCalendarPopup(True)
        date_layout.addWidget(date_widget)
        date_layout.addStretch(1)
        one_off_layout.addLayout(date_layout)

        income_date_layout = QHBoxLayout()
        income_date_layout.addWidget(QLabel("Income Date: "))
        income_date_widget = QComboBox()
        income_date_widget.addItems([x.strftime("%Y-%m-%d") for x in self.schedule.sorted_income_dates])
        income_date_layout.addWidget(income_date_widget)
        income_date_layout.addStretch(1)
        one_off_layout.addLayout(income_date_layout)

        account_layout = QHBoxLayout()
        account_layout.addWidget(QLabel("Account: "))
        account_widget = QComboBox()
        accounts = self.db.fetch_accounts(self.selected_profile.id)
        for account in accounts:
            account_widget.addItem(account.name)
        account_widget.setEnabled(False)
        account_layout.addWidget(account_widget)
        account_layout.addStretch(1)

        paid_layout = QHBoxLayout()
        paid_layout.addWidget(QLabel("Paid: "))
        paid_widget = QCheckBox()
        paid_widget.checkStateChanged.connect(lambda: account_widget.setEnabled(paid_widget.isChecked()))
        paid_layout.addWidget(paid_widget)
        paid_layout.addStretch(1)
        one_off_layout.addLayout(paid_layout)

        one_off_layout.addLayout(account_layout)

        one_off_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(lambda: one_off_dialog.close())
        buttons_layout.addWidget(cancel_button)
        ok_button = QPushButton("Save")
        buttons_layout.addWidget(ok_button)
        one_off_layout.addLayout(buttons_layout)

        one_off_dialog.setLayout(one_off_layout)
        one_off_dialog.exec()

    def fix_unscheduled(self):
        print("TODO: fix unscheduled")
        for entry in self.schedule.unscheduled_entries:
            print(entry)

    def set_savings_items(self):
        knapsack = DefaultKnapsack(self.db, self.selected_profile.id)
        savings_items: list[ExtrapolationItem] = knapsack.compute_savings()

        savings_dialog = QDialog()
        savings_layout = QVBoxLayout()

        for item in savings_items:
            print(item)

        savings_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        cancel_button = QPushButton("Cancel")
        buttons_layout.addWidget(cancel_button)
        ok_button = QPushButton("Save")
        buttons_layout.addWidget(ok_button)
        savings_layout.addLayout(buttons_layout)

        savings_dialog.setLayout(savings_layout)
        savings_dialog.exec()

    def extrapolate_budget(self, vertical_layout):
        knapsack = DefaultKnapsack(self.db, self.selected_profile.id)
        today = date.today()
        in_one_year = today + timedelta(days=365)
        knapsack.run(today, in_one_year)
        knapsack.save_schedule()
        self.schedule.fetch_schedule(self.db, self.selected_profile.id)
        self.schedule.build_schedule()
        self.render_schedule(self.schedule_vertical_layout)

    def render_schedule(self, vertical_layout):
        self.grid_entries = {}

        date_strings = []
        for income_date in self.schedule.sorted_income_dates:
            date_strings.append(income_date.strftime("%Y-%m-%d"))

        if self.schedule.expense_budget_items is not None and self.schedule_widget is not None:
            vertical_layout.removeWidget(self.schedule_widget)
            del self.schedule_widget

        self.schedule_widget = QTableWidget()
        self.schedule_widget.setColumnCount(len(self.schedule.sorted_income_dates))
        self.schedule_widget.setHorizontalHeaderLabels(date_strings)
        self.schedule_widget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.schedule_widget.horizontalHeader().setStretchLastSection(True)
        # row for each expense plus one for income, a subtotal, and a leftover, and carryover
        self.schedule_widget.setRowCount(len(self.schedule.expense_budget_items) + 4)
        self.schedule_widget.itemClicked.connect(self.cell_clicked)

        idx = 0

        # Render carryover row
        self.schedule_widget.setVerticalHeaderItem(idx, QTableWidgetItem("Carryover"))
        cidx = 0
        for income_date in self.schedule.sorted_income_dates:
            schedule_column = self.schedule.columns.get(
                income_date.strftime("%Y-%m-%d"), None
            )
            if schedule_column is None:
                self.schedule_widget.setItem(
                    idx, cidx, self.create_cell(income_date, None)
                )
                cidx += 1
                continue

            self.schedule_widget.setItem(
                idx,
                cidx,
                self.create_cell(
                    income_date, schedule_column.starting_balance, True, True
                ),
            )
            cidx += 1
        idx += 1

        # Render income row, just one for now
        for budget_items in self.schedule.income_budget_items:
            cidx = 0
            self.schedule_widget.setVerticalHeaderItem(
                idx, QTableWidgetItem(budget_items.name)
            )

            for income_date in self.schedule.sorted_income_dates:
                schedule_column = self.schedule.columns.get(
                    income_date.strftime("%Y-%m-%d"), None
                )
                if schedule_column is None:
                    self.schedule_widget.setItem(
                        idx, cidx, self.create_cell(income_date, None)
                    )
                    cidx += 1
                    continue

                if idx == 1:
                    # matching = next((x for x in schedule_column.expenses if x.name == budget_items.name), None)
                    # TODO: Stop being lazy and let multiple expenses happen
                    if len(schedule_column.incomes) > 0:
                        self.grid_entries[(idx, cidx)] = income_entry = (
                            schedule_column.incomes[0]
                        )
                        # self.grid_entries[(idx, cidx)] = schedule_column.income
                        self.schedule_widget.setItem(
                            idx,
                            cidx,
                            self.create_cell(
                                income_date,
                                income_entry.total(),  # + schedule_column.starting_balance,
                                True,
                                True,
                                income_entry.all_paid(),
                            ),
                        )
                    else:
                        self.schedule_widget.setItem(
                            idx, cidx, self.create_cell(income_date, None)
                        )
                    cidx += 1
            idx += 1

        # Render expense rows
        for budget_item in self.schedule.expense_budget_items:
            cidx = 0

            self.schedule_widget.setVerticalHeaderItem(
                idx, QTableWidgetItem(budget_item.name)
            )

            for income_date in self.schedule.sorted_income_dates:
                schedule_column = self.schedule.columns.get(
                    income_date.strftime("%Y-%m-%d"), None
                )
                if schedule_column is None:
                    self.schedule_widget.setItem(
                        idx, cidx, self.create_cell(income_date, None)
                    )
                    cidx += 1
                    continue

                matching = next(
                    (
                        x
                        for x in schedule_column.expenses
                        if x.budget_item.id == budget_item.id
                    ),
                    None,
                )
                if income_date.strftime("%Y-%m-%d") == '2025-07-01' and budget_item.name == 'Gas' and matching is not None:
                    print("\tDEBUG: Found Gas entry", matching.all_paid())
                if matching is not None:
                    self.grid_entries[(idx, cidx)] = matching
                    self.schedule_widget.setItem(
                        idx,
                        cidx,
                        self.create_cell(
                            income_date,
                            matching.total(),
                            False,
                            False,
                            matching.all_paid(),
                        ),
                    )
                else:
                    self.schedule_widget.setItem(
                        idx, cidx, self.create_cell(income_date, None)
                    )
                cidx += 1
            idx += 1

        # Render subtotal row
        self.schedule_widget.setVerticalHeaderItem(idx, QTableWidgetItem("Subtotal"))
        cidx = 0
        for income_date in self.schedule.sorted_income_dates:
            schedule_column = self.schedule.columns.get(
                income_date.strftime("%Y-%m-%d"), None
            )
            if schedule_column is not None:
                self.schedule_widget.setItem(
                    idx,
                    cidx,
                    self.create_cell(
                        income_date, schedule_column.expenses_total(), True, True
                    ),
                )
            cidx += 1
        idx += 1

        # Render leftover row
        self.schedule_widget.setVerticalHeaderItem(idx, QTableWidgetItem("Leftover"))
        cidx = 0
        for income_date in self.schedule.sorted_income_dates:
            schedule_column = self.schedule.columns.get(
                income_date.strftime("%Y-%m-%d"), None
            )
            self.schedule_widget.setItem(
                idx,
                cidx,
                self.create_cell(income_date, schedule_column.total(), True, True),
            )
            cidx += 1
        idx += 1

        vertical_layout.addWidget(self.schedule_widget)
