from datetime import date, timedelta
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QScrollArea,
    QDialog,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database.database import Database
from database.profile import Profile
from shedule.schedule import Schedule
from services import LedgerService


class Dashboard(QWidget):
    db: Database = None
    selected_profile: Profile = None
    schedule: Schedule = None
    ledger_service: LedgerService = None

    def __init__(self, db, selected_profile):
        super().__init__()
        self.db = db
        self.selected_profile = selected_profile
        self.ledger_service = LedgerService(db)

        self.schedule = Schedule()
        self.schedule.fetch_schedule(self.db, self.selected_profile.id)
        self.schedule.build_schedule()

        self._build_ui()

    def _build_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        self._render_header()
        self._render_safe_to_spend()
        self._render_overdue_items()
        self._render_upcoming_items()
        self._render_quick_add_expense()
        self._render_pay_period_summary()

        self.content_layout.addStretch(1)
        content.setLayout(self.content_layout)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        self.setLayout(outer_layout)

    def _section_font(self):
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        return f

    def _field_font(self):
        f = QFont()
        f.setPointSize(11)
        f.setBold(True)
        return f

    def _card_frame(self):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { border: 1px solid #546e7a; border-radius: 8px; padding: 16px; }"
        )
        return frame

    def _button_style(self):
        return (
            "padding: 10px 20px; border: 1px solid #546e7a; "
            "border-radius: 5px; font-size: 13px; font-weight: bold;"
        )

    # ── 1. Header ──────────────────────────────────────────────

    def _render_header(self):
        title = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        self.content_layout.addWidget(title)

        subtitle = QLabel(date.today().strftime("%A, %B %d, %Y"))
        subtitle.setStyleSheet("font-size: 13px; color: #90a4ae;")
        self.content_layout.addWidget(subtitle)

    # ── 2. Safe to Spend ───────────────────────────────────────

    def _render_safe_to_spend(self):
        today = date.today()
        current_column = None
        current_key = None

        first_column = None
        first_key = None
        for income_date in self.schedule.sorted_income_dates:
            key = income_date.strftime("%Y-%m-%d")
            col = self.schedule.columns.get(key)
            if col is None:
                continue
            if first_column is None:
                first_column = col
                first_key = key
            # Find the column whose income_date is <= today and is the latest such
            if income_date <= today:
                current_column = col
                current_key = key

        # Fall back to the first column if all dates are in the future
        if current_column is None and first_column is not None:
            current_column = first_column
            current_key = first_key

        frame = self._card_frame()
        vl = QVBoxLayout()
        vl.setSpacing(8)

        header = QLabel("Safe to Spend")
        header.setFont(self._section_font())
        vl.addWidget(header)

        if current_column is not None:
            safe_to_spend = current_column.total()
            color = "#4caf50" if safe_to_spend >= 0 else "#f44336"

            amount_label = QLabel(f"${safe_to_spend:,.2f}")
            amount_font = QFont()
            amount_font.setPointSize(28)
            amount_font.setBold(True)
            amount_label.setFont(amount_font)
            amount_label.setStyleSheet(f"color: {color};")
            vl.addWidget(amount_label)

            income_date_label = QLabel(
                f"Pay period starting: {current_column.income_date.strftime('%b %d, %Y')}"
            )
            income_date_label.setFont(self._field_font())
            vl.addWidget(income_date_label)

            ending = current_column.total()
            ending_label = QLabel(f"Ending balance: ${ending:,.2f}")
            ending_label.setStyleSheet("font-size: 13px; color: #90a4ae;")
            vl.addWidget(ending_label)
        else:
            no_data = QLabel("No pay period data available. Run Extrapolation first.")
            no_data.setStyleSheet("font-size: 13px; color: #90a4ae;")
            vl.addWidget(no_data)

        frame.setLayout(vl)
        self.content_layout.addWidget(frame)

    # ── 3. Overdue Items ───────────────────────────────────────

    def _get_unpaid_items(self):
        """Return a list of (extrapolation_item, budget_item_name) tuples for unpaid items."""
        items = []
        budget_items = {bi.id: bi for bi in self.schedule.budget_item_list}
        for ext in self.schedule.extrapolation_items:
            if ext.ledger_entry_id is not None:
                continue
            name = ext.name
            if not name and ext.budget_item_id:
                bi = budget_items.get(ext.budget_item_id)
                name = bi.name if bi else f"Item #{ext.budget_item_id}"
            if not name:
                name = "Unknown Item"
            items.append((ext, name))
        return items

    def _render_overdue_items(self):
        today = date.today()
        unpaid = self._get_unpaid_items()
        overdue = [(ext, name) for ext, name in unpaid if ext.due_date and ext.due_date < today]

        if not overdue:
            return

        frame = self._card_frame()
        frame.setStyleSheet(
            "QFrame { border: 1px solid #f44336; border-radius: 8px; padding: 16px; }"
        )
        vl = QVBoxLayout()
        vl.setSpacing(8)

        header = QLabel(f"Overdue Items ({len(overdue)})")
        header.setFont(self._section_font())
        header.setStyleSheet("color: #f44336;")
        vl.addWidget(header)

        for ext, name in overdue:
            row = QHBoxLayout()
            row.setSpacing(12)

            name_label = QLabel(name)
            name_label.setFont(self._field_font())
            row.addWidget(name_label)

            amount_label = QLabel(f"${abs(float(ext.amount)):,.2f}")
            amount_label.setStyleSheet("font-size: 13px; color: #f44336; font-weight: bold;")
            row.addWidget(amount_label)

            due_label = QLabel(f"Due: {ext.due_date.strftime('%b %d')}")
            due_label.setStyleSheet("font-size: 12px; color: #90a4ae;")
            row.addWidget(due_label)

            row.addStretch(1)

            pay_btn = QPushButton("Mark Paid")
            pay_btn.setStyleSheet(self._button_style())
            pay_btn.clicked.connect(
                lambda checked=False, item=ext: self._mark_paid(item)
            )
            row.addWidget(pay_btn)

            vl.addLayout(row)

        frame.setLayout(vl)
        self.content_layout.addWidget(frame)

    # ── 4. Upcoming Items (next 7 days) ───────────────────────

    def _render_upcoming_items(self):
        today = date.today()
        horizon = today + timedelta(days=7)
        unpaid = self._get_unpaid_items()
        upcoming = [
            (ext, name)
            for ext, name in unpaid
            if ext.due_date and today <= ext.due_date <= horizon
        ]

        if not upcoming:
            return

        frame = self._card_frame()
        vl = QVBoxLayout()
        vl.setSpacing(8)

        header = QLabel(f"Upcoming Items - Next 7 Days ({len(upcoming)})")
        header.setFont(self._section_font())
        vl.addWidget(header)

        for ext, name in upcoming:
            days_until = (ext.due_date - today).days
            row = QHBoxLayout()
            row.setSpacing(12)

            name_label = QLabel(name)
            name_label.setFont(self._field_font())
            row.addWidget(name_label)

            amount_label = QLabel(f"${abs(float(ext.amount)):,.2f}")
            amount_label.setStyleSheet("font-size: 13px; font-weight: bold;")
            row.addWidget(amount_label)

            due_label = QLabel(f"Due: {ext.due_date.strftime('%b %d')}")
            due_label.setStyleSheet("font-size: 12px; color: #90a4ae;")
            row.addWidget(due_label)

            days_label = QLabel(
                f"{'Today' if days_until == 0 else f'In {days_until} day' + ('s' if days_until != 1 else '')}"
            )
            days_label.setStyleSheet("font-size: 12px; color: #90a4ae;")
            row.addWidget(days_label)

            row.addStretch(1)

            pay_btn = QPushButton("Mark Paid")
            pay_btn.setStyleSheet(self._button_style())
            pay_btn.clicked.connect(
                lambda checked=False, item=ext: self._mark_paid(item)
            )
            row.addWidget(pay_btn)

            vl.addLayout(row)

        frame.setLayout(vl)
        self.content_layout.addWidget(frame)

    # ── 5. Quick Add Expense ───────────────────────────────────

    def _render_quick_add_expense(self):
        frame = self._card_frame()
        vl = QVBoxLayout()
        vl.setSpacing(10)

        header = QLabel("Quick Add Expense")
        header.setFont(self._section_font())
        vl.addWidget(header)

        input_style = "padding: 10px; font-size: 14px;"
        input_height = 40

        form_row = QHBoxLayout()
        form_row.setSpacing(10)

        name_label = QLabel("Name")
        name_label.setFont(self._field_font())
        form_row.addWidget(name_label)

        self.quick_name = QLineEdit()
        self.quick_name.setPlaceholderText("e.g., Coffee")
        self.quick_name.setStyleSheet(input_style)
        self.quick_name.setMinimumHeight(input_height)
        form_row.addWidget(self.quick_name)

        amount_label = QLabel("Amount")
        amount_label.setFont(self._field_font())
        form_row.addWidget(amount_label)

        self.quick_amount = QLineEdit()
        self.quick_amount.setPlaceholderText("0.00")
        self.quick_amount.setStyleSheet(input_style)
        self.quick_amount.setMinimumHeight(input_height)
        form_row.addWidget(self.quick_amount)

        acct_label = QLabel("Account")
        acct_label.setFont(self._field_font())
        form_row.addWidget(acct_label)

        self.quick_account = QComboBox()
        self.quick_account.setStyleSheet(input_style)
        self.quick_account.setMinimumHeight(input_height)
        accounts = self.db.fetch_accounts(self.selected_profile.id)
        for acct in accounts:
            self.quick_account.addItem(acct.name, acct.id)
        form_row.addWidget(self.quick_account)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(self._button_style())
        save_btn.setMinimumHeight(input_height)
        save_btn.clicked.connect(self._quick_add_save)
        form_row.addWidget(save_btn)

        vl.addLayout(form_row)
        frame.setLayout(vl)
        self.content_layout.addWidget(frame)

    def _quick_add_save(self):
        name = self.quick_name.text().strip()
        amount_text = self.quick_amount.text().strip()
        account_id = self.quick_account.currentData()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter an expense name.")
            return
        try:
            amount = float(amount_text)
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid amount.")
            return
        if account_id is None:
            QMessageBox.warning(self, "Invalid Input", "Please select an account.")
            return

        today = date.today()
        today_str = today.isoformat()

        try:
            # Find the current income_date for the one-off item
            income_date = None
            for inc_date in self.schedule.sorted_income_dates:
                if inc_date <= today:
                    income_date = inc_date
            income_date_str = income_date.isoformat() if income_date else today_str

            # Create ledger entry
            self.db.create_ledger_entry(
                name=name,
                date=today,
                incomeDate=income_date if income_date else today,
                type="Expense",
                amount=-amount,
                accountId=account_id,
            )

            # Create one-off extrapolation item for today
            self.db.create_extrapolation_item(
                self.selected_profile.id,
                today_str,
                -amount,
                income_date_str,
                None,
                category="one_off",
                name=name,
            )

            QMessageBox.information(
                self, "Success", f"Expense '{name}' for ${amount:,.2f} saved."
            )
            self.quick_name.clear()
            self.quick_amount.clear()
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save expense: {str(e)}")

    # ── 6. Pay Period Summary ──────────────────────────────────

    def _render_pay_period_summary(self):
        if not self.schedule.sorted_income_dates:
            return

        frame = self._card_frame()
        vl = QVBoxLayout()
        vl.setSpacing(8)

        header = QLabel("Pay Period Summary")
        header.setFont(self._section_font())
        vl.addWidget(header)

        for income_date in self.schedule.sorted_income_dates:
            key = income_date.strftime("%Y-%m-%d")
            col = self.schedule.columns.get(key)
            if col is None:
                continue

            income_total = col.income_total()
            expenses_total = col.expenses_total()
            safe = col.total()
            color = "#4caf50" if safe >= 0 else "#f44336"

            row = QHBoxLayout()
            row.setSpacing(16)

            date_label = QLabel(income_date.strftime("%b %d, %Y"))
            date_label.setFont(self._field_font())
            date_label.setFixedWidth(120)
            row.addWidget(date_label)

            inc_label = QLabel(f"Income: ${income_total:,.2f}")
            inc_label.setStyleSheet("font-size: 12px; color: #4caf50;")
            inc_label.setFixedWidth(160)
            row.addWidget(inc_label)

            exp_label = QLabel(f"Expenses: ${abs(expenses_total):,.2f}")
            exp_label.setStyleSheet("font-size: 12px; color: #f44336;")
            exp_label.setFixedWidth(160)
            row.addWidget(exp_label)

            safe_label = QLabel(f"Safe: ${safe:,.2f}")
            safe_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {color};")
            row.addWidget(safe_label)

            row.addStretch(1)
            vl.addLayout(row)

        frame.setLayout(vl)
        self.content_layout.addWidget(frame)

    # ── Mark Paid dialog ───────────────────────────────────────

    def _mark_paid(self, extrap_item):
        accounts = self.db.fetch_accounts(self.selected_profile.id)
        if not accounts:
            QMessageBox.warning(
                self, "No Accounts", "Please create an account first in the Accounts tab."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Mark Item Paid")
        dialog.setMinimumWidth(300)
        dl = QVBoxLayout()
        dl.setSpacing(12)
        dl.setContentsMargins(20, 20, 20, 20)

        label = QLabel("Select account for payment:")
        label.setFont(self._field_font())
        dl.addWidget(label)

        account_combo = QComboBox()
        account_combo.setStyleSheet("padding: 10px; font-size: 14px;")
        account_combo.setMinimumHeight(40)
        for acct in accounts:
            account_combo.addItem(acct.name, acct.id)
        dl.addWidget(account_combo)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._button_style())
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setStyleSheet(self._button_style())
        confirm_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(confirm_btn)

        btn_row.addStretch(1)
        dl.addLayout(btn_row)
        dialog.setLayout(dl)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            account_id = account_combo.currentData()
            try:
                self.ledger_service.mark_extrapolation_item_paid(
                    extrap_item.id, account_id, date.today().isoformat()
                )
                QMessageBox.information(self, "Success", "Item marked as paid.")
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to mark paid: {str(e)}")

    # ── Refresh ────────────────────────────────────────────────

    def _refresh(self):
        """Rebuild the schedule and UI."""
        self.schedule = Schedule()
        self.schedule.fetch_schedule(self.db, self.selected_profile.id)
        self.schedule.build_schedule()

        # Clear and rebuild
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._render_header()
        self._render_safe_to_spend()
        self._render_overdue_items()
        self._render_upcoming_items()
        self._render_quick_add_expense()
        self._render_pay_period_summary()
        self.content_layout.addStretch(1)
