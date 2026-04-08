from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QComboBox,
    QStackedWidget,
    QMessageBox,
    QLabel,
    QHeaderView,
    QDialog,
    QScrollArea,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from database.database import Database
from database.debt import Debt
from database.profile import Profile
from services.debt_service import DebtService
from ui.onboarding import HelpIcon, HELP_TEXTS


class Debts(QStackedWidget):
    payments_saved = pyqtSignal()

    db: Database = None
    selected_profile: Profile = None
    debts: list = None
    editing_debt: Debt = None

    def __init__(self, db, selected_profile):
        super().__init__()
        self.db = db
        self.selected_profile = selected_profile
        self.debts = []
        self.editing_debt = None
        self.refresh()

    def _clear_all_widgets(self):
        while self.count() > 0:
            w = self.widget(0)
            self.removeWidget(w)
            w.deleteLater()

    def refresh(self):
        self._clear_all_widgets()
        self.render_list()
        self.render_form()

    def render_list(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vl = QVBoxLayout(container)

        title_row = QHBoxLayout()
        title = QLabel("Debts")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title_row.addWidget(title)
        title_row.addWidget(HelpIcon(HELP_TEXTS["debts"]))
        title_row.addStretch(1)
        vl.addLayout(title_row)

        self.debts = self.db.fetch_debts(self.selected_profile.id)

        if not self.debts:
            empty = QLabel(
                "No debts added yet.\n\n"
                "Track loans, credit cards, and other debts here.\n"
                "Budgie can compute optimal payment plans from your budget surplus.\n\n"
                "Click 'Add Debt' below to get started."
            )
            empty.setWordWrap(True)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #999; padding: 20px;")
            vl.addWidget(empty)
        else:
            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels([
                "Name", "Total", "Remaining", "Min Payment", "Interest %", "Actions"
            ])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            table.setRowCount(len(self.debts))

            for row, debt in enumerate(self.debts):
                table.setItem(row, 0, QTableWidgetItem(debt.name))
                table.setItem(row, 1, QTableWidgetItem(f"${debt.total_amount:,.2f}"))
                table.setItem(row, 2, QTableWidgetItem(f"${debt.remaining_amount:,.2f}"))
                table.setItem(row, 3, QTableWidgetItem(f"${debt.min_payment:,.2f}"))
                table.setItem(row, 4, QTableWidgetItem(f"{debt.interest_rate:.1f}%"))

                actions = QWidget()
                actions_layout = QHBoxLayout(actions)
                actions_layout.setContentsMargins(4, 0, 4, 0)

                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("padding: 4px 10px; border: 1px solid #546e7a; border-radius: 3px;")
                edit_btn.clicked.connect(lambda _, d=debt: self.edit_debt(d))
                actions_layout.addWidget(edit_btn)

                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("padding: 4px 10px; border: 1px solid #546e7a; border-radius: 3px; color: #ef5350;")
                delete_btn.clicked.connect(lambda _, d=debt: self.delete_debt(d))
                actions_layout.addWidget(delete_btn)

                table.setCellWidget(row, 5, actions)

            table.setMinimumHeight(min(len(self.debts) * 45 + 40, 300))
            vl.addWidget(table)

        # Action buttons
        btn_row = QHBoxLayout()

        add_btn = QPushButton("+ Add Debt")
        add_btn.setStyleSheet("font-weight: bold; padding: 8px 16px; border: 1px solid #546e7a; border-radius: 4px;")
        add_btn.clicked.connect(lambda: self.edit_debt(None))
        btn_row.addWidget(add_btn)

        compute_btn = QPushButton("Compute Payments")
        compute_btn.setStyleSheet("padding: 8px 16px; border: 1px solid #546e7a; border-radius: 4px;")
        compute_btn.clicked.connect(self.compute_payments)
        btn_row.addWidget(compute_btn)

        btn_row.addStretch(1)
        vl.addLayout(btn_row)

        vl.addStretch(1)
        scroll.setWidget(container)
        self.addWidget(scroll)

    def render_form(self, debt=None):
        widget = QWidget()
        widget.setMaximumWidth(600)
        vl = QVBoxLayout(widget)
        vl.setSpacing(6)
        vl.setContentsMargins(24, 16, 24, 16)

        input_style = "padding: 10px; font-size: 14px;"
        input_height = 40
        label_font = QFont()
        label_font.setPointSize(11)
        label_font.setBold(True)
        btn_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"

        # Back button
        back_btn = QPushButton("Back to Debts")
        back_btn.setStyleSheet("padding: 8px 16px; border: 1px solid #546e7a; border-radius: 5px; font-size: 12px;")
        back_btn.setMaximumWidth(160)
        back_btn.clicked.connect(lambda: self.setCurrentIndex(0))
        vl.addWidget(back_btn)
        vl.addSpacing(8)

        title_text = "Edit Debt" if debt else "Add Debt"
        title = QLabel(title_text)
        title_font_obj = QFont()
        title_font_obj.setPointSize(18)
        title_font_obj.setBold(True)
        title.setFont(title_font_obj)
        vl.addWidget(title)
        vl.addSpacing(12)

        def add_field_label(text):
            lbl = QLabel(text)
            lbl.setFont(label_font)
            vl.addWidget(lbl)

        add_field_label("Name")
        name_input = QLineEdit(debt.name if debt else "")
        name_input.setPlaceholderText("e.g., Credit Card, Student Loan")
        name_input.setStyleSheet(input_style)
        name_input.setMinimumHeight(input_height)
        vl.addWidget(name_input)
        vl.addSpacing(8)

        add_field_label("Total Amount")
        total_input = QLineEdit(str(debt.total_amount) if debt else "")
        total_input.setPlaceholderText("e.g. 5000")
        total_input.setStyleSheet(input_style)
        total_input.setMinimumHeight(input_height)
        vl.addWidget(total_input)
        vl.addSpacing(8)

        add_field_label("Remaining Amount")
        remaining_input = QLineEdit(str(debt.remaining_amount) if debt else "")
        remaining_input.setPlaceholderText("e.g. 3000")
        remaining_input.setStyleSheet(input_style)
        remaining_input.setMinimumHeight(input_height)
        vl.addWidget(remaining_input)
        vl.addSpacing(8)

        add_field_label("Minimum Monthly Payment")
        min_input = QLineEdit(str(debt.min_payment) if debt else "")
        min_input.setPlaceholderText("e.g. 100")
        min_input.setStyleSheet(input_style)
        min_input.setMinimumHeight(input_height)
        vl.addWidget(min_input)
        vl.addSpacing(8)

        add_field_label("Interest Rate (%)")
        rate_input = QLineEdit(str(debt.interest_rate) if debt else "0")
        rate_input.setPlaceholderText("e.g. 19.99")
        rate_input.setStyleSheet(input_style)
        rate_input.setMinimumHeight(input_height)
        vl.addWidget(rate_input)

        vl.addSpacing(20)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(btn_style)
        save_btn.setMinimumHeight(44)
        save_btn.clicked.connect(lambda: self.save_debt(
            debt,
            name_input.text(),
            total_input.text(),
            remaining_input.text(),
            min_input.text(),
            rate_input.text(),
        ))
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(btn_style)
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(lambda: self.setCurrentIndex(0))
        btn_row.addWidget(cancel_btn)

        btn_row.addStretch(1)
        vl.addLayout(btn_row)
        vl.addStretch(1)

        self.addWidget(widget)

    def edit_debt(self, debt):
        self._clear_all_widgets()
        self.render_list()
        self.render_form(debt)
        self.setCurrentIndex(1)

    def save_debt(self, existing_debt, name, total, remaining, min_pay, rate):
        try:
            total_f = float(total)
            remaining_f = float(remaining)
            min_f = float(min_pay)
            rate_f = float(rate)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers.")
            return

        if not name.strip():
            QMessageBox.warning(self, "Invalid Input", "Name cannot be empty.")
            return

        try:
            if existing_debt:
                self.db.update_debt(
                    existing_debt.id, name, total_f, remaining_f, min_f, rate_f
                )
                QMessageBox.information(self, "Success", f"Debt '{name}' updated successfully!")
            else:
                self.db.create_debt(
                    self.selected_profile.id, name, total_f, remaining_f, min_f, rate_f
                )
                QMessageBox.information(self, "Success", f"Debt '{name}' created successfully!")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save debt: {str(e)}")

    def delete_debt(self, debt):
        reply = QMessageBox.question(
            self, "Delete Debt",
            f"Are you sure you want to delete '{debt.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_debt(debt.id)
                QMessageBox.information(self, "Success", f"Debt '{debt.name}' has been deleted.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete debt: {str(e)}")

    def compute_payments(self):
        if not self.debts:
            QMessageBox.information(self, "No Debts", "Add debts first before computing payments.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Compute Debt Payments")
        dialog.resize(700, 550)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Savings Margin (keep this much surplus per period):"))
        margin_input = QLineEdit("50")
        layout.addWidget(margin_input)

        result_label = QLabel("")
        result_label.setWordWrap(True)
        layout.addWidget(result_label)

        # Results table (hidden initially) - columns: Debt, Income Date, Amount, Remove
        result_table = QTableWidget()
        result_table.setColumnCount(4)
        result_table.setHorizontalHeaderLabels(["Debt", "Income Date", "Amount", ""])
        result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        result_table.setVisible(False)
        layout.addWidget(result_table)

        # Summary widget (hidden initially)
        summary_container = QWidget()
        summary_layout = QVBoxLayout(summary_container)
        summary_layout.setContentsMargins(0, 8, 0, 0)
        summary_container.setVisible(False)
        layout.addWidget(summary_container)

        computed_payments = []
        available_income_dates = []

        def populate_table():
            """Rebuild the table from computed_payments list."""
            result_table.setRowCount(len(computed_payments))
            for row, p in enumerate(computed_payments):
                # Debt dropdown
                debt_combo = QComboBox()
                for d in self.debts:
                    debt_combo.addItem(d.name, d.id)
                # Select current debt
                for i in range(debt_combo.count()):
                    if debt_combo.itemData(i) == p["debt_id"]:
                        debt_combo.setCurrentIndex(i)
                        break
                debt_combo.currentIndexChanged.connect(
                    lambda _, r=row, combo=debt_combo: on_debt_changed(r, combo)
                )
                result_table.setCellWidget(row, 0, debt_combo)

                # Income date dropdown
                date_combo = QComboBox()
                for d in available_income_dates:
                    date_combo.addItem(d)
                date_combo.setEditable(True)
                date_combo.setCurrentText(str(p["income_date"]))
                date_combo.currentTextChanged.connect(
                    lambda val, r=row: on_date_changed(r, val)
                )
                result_table.setCellWidget(row, 1, date_combo)

                # Editable amount spinner
                amount_spin = QDoubleSpinBox()
                amount_spin.setRange(0, 999999999)
                amount_spin.setDecimals(2)
                amount_spin.setPrefix("$")
                amount_spin.setValue(p["amount"])
                amount_spin.valueChanged.connect(
                    lambda val, r=row: on_amount_changed(r, val)
                )
                result_table.setCellWidget(row, 2, amount_spin)

                # Remove button
                remove_btn = QPushButton("Remove")
                remove_btn.setStyleSheet("""
                    QPushButton {
                        padding: 4px 8px;
                        border: 1px solid #546e7a;
                        border-radius: 3px;
                        font-size: 11px;
                        color: #ef5350;
                    }
                """)
                remove_btn.clicked.connect(lambda _, r=row: remove_payment(r))
                result_table.setCellWidget(row, 3, remove_btn)

            result_table.setVisible(len(computed_payments) > 0)
            update_summary()

        def on_debt_changed(row, combo):
            if row < len(computed_payments):
                computed_payments[row]["debt_id"] = combo.currentData()
                computed_payments[row]["debt_name"] = combo.currentText()
                update_summary()

        def on_date_changed(row, val):
            if row < len(computed_payments):
                computed_payments[row]["income_date"] = val

        def on_amount_changed(row, val):
            if row < len(computed_payments):
                computed_payments[row]["amount"] = round(val, 2)
                update_summary()

        def remove_payment(row):
            if row < len(computed_payments):
                computed_payments.pop(row)
                populate_table()

        def add_payment():
            if not self.debts:
                return
            first_debt = self.debts[0]
            income_date = available_income_dates[0] if available_income_dates else ""
            computed_payments.append({
                "debt_id": first_debt.id,
                "debt_name": first_debt.name,
                "amount": 0.0,
                "income_date": income_date,
            })
            populate_table()

        def update_summary():
            """Rebuild the color-coded per-debt summary."""
            # Clear existing summary labels
            while summary_layout.count() > 0:
                item = summary_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            title = QLabel("Payment Summary")
            title_font = QFont()
            title_font.setBold(True)
            title.setFont(title_font)
            summary_layout.addWidget(title)

            # Sum payments per debt
            totals = {}
            for p in computed_payments:
                totals[p["debt_id"]] = totals.get(p["debt_id"], 0) + p["amount"]

            for debt in self.debts:
                if debt.id not in totals:
                    continue
                total_payments = totals[debt.id]
                remaining = float(debt.remaining_amount)
                diff = abs(total_payments - remaining)

                if diff < 0.01:
                    status = "exact"
                    color = "#66bb6a"
                    label_text = "Exact"
                elif total_payments < remaining:
                    status = "under"
                    color = "#ef5350"
                    label_text = f"Underpaying (-${remaining - total_payments:,.2f})"
                else:
                    status = "over"
                    color = "#ffb74d"
                    label_text = f"Overpaying (+${total_payments - remaining:,.2f})"

                row_widget = QWidget()
                row_widget.setStyleSheet(
                    f"border-left: 4px solid {color}; padding: 4px 8px;"
                )
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(8, 2, 8, 2)

                name_label = QLabel(debt.name)
                name_label.setStyleSheet("font-weight: bold; font-size: 12px; border: none;")
                row_layout.addWidget(name_label)

                row_layout.addStretch(1)

                amounts_label = QLabel(f"${total_payments:,.2f} / ${remaining:,.2f}")
                amounts_label.setStyleSheet("font-size: 12px; border: none;")
                row_layout.addWidget(amounts_label)

                status_label = QLabel(label_text)
                status_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color}; border: none;")
                row_layout.addWidget(status_label)

                summary_layout.addWidget(row_widget)

            summary_container.setVisible(len(computed_payments) > 0)

        def do_compute():
            nonlocal computed_payments, available_income_dates
            try:
                margin = float(margin_input.text())
            except ValueError:
                result_label.setText("Please enter a valid number for savings margin.")
                return

            service = DebtService(self.db)
            payments = service.compute_debt_payments(self.selected_profile.id, margin)
            computed_payments = payments

            # Collect unique income dates for dropdowns
            available_income_dates = sorted(list(set(
                str(p["income_date"]) for p in payments
            )))

            if not payments:
                result_label.setText("No surplus available for debt payments with the given margin.")
                result_table.setVisible(False)
                summary_container.setVisible(False)
                return

            result_label.setText(f"Found {len(payments)} potential payment(s) — edit amounts, add, or remove as needed:")
            populate_table()

        def do_save():
            if not computed_payments:
                return
            service = DebtService(self.db)
            count = service.save_debt_payments(self.selected_profile.id, computed_payments)
            QMessageBox.information(dialog, "Saved", f"Saved {count} debt payment(s) to the schedule.")
            self.payments_saved.emit()
            dialog.accept()

        # Buttons
        btn_row = QHBoxLayout()
        compute_btn = QPushButton("Compute")
        compute_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #546e7a;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        compute_btn.clicked.connect(do_compute)
        btn_row.addWidget(compute_btn)

        add_btn = QPushButton("+ Add Payment")
        add_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #546e7a;
                border-radius: 4px;
            }
        """)
        add_btn.clicked.connect(add_payment)
        btn_row.addWidget(add_btn)

        save_btn = QPushButton("Save Payments")
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #546e7a;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        save_btn.clicked.connect(do_save)
        btn_row.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #546e7a;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)
        dialog.exec()
