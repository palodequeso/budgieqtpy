from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QComboBox,
    QStackedWidget,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QDateEdit,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont
from database.account import Account
from database.database import Database
from database.ledger_entry import LedgerEntry
from database.profile import Profile
from ui.onboarding import HelpIcon, HELP_TEXTS


class Accounts(QStackedWidget):
    db: Database = None
    selected_profile: Profile = None
    accounts: list[Account] = None
    account_widget: QWidget = None

    def __init__(self, db, selected_profile):
        super().__init__()
        self.db = db
        self.selected_profile = selected_profile
        self.accounts = self.db.fetch_accounts(self.selected_profile.id)
        self.account_widget = None
        self.render_accounts()
        self.render_create_account()

    def render_account(self, account):
        widget = QWidget()
        
        # Determine icon and color based on account type
        account_icons = {
            "Checking": "[C]",
            "Savings": "[S]",
            "Credit Card": "[CC]"
        }
        icon = account_icons.get(account.account_type, "[A]")

        widget.setStyleSheet("""
            QWidget {
                border: 2px solid;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        widget.setMinimumWidth(280)
        widget.setMinimumHeight(200)
        widget.setMaximumWidth(300)

        vl = QVBoxLayout()
        vl.setSpacing(8)

        # Account name with icon
        name_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        name_layout.addWidget(icon_label)
        
        name = QLabel(account.name)
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        name.setFont(name_font)
        name_layout.addWidget(name)
        name_layout.addStretch(1)
        vl.addLayout(name_layout)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("border: none;")
        vl.addWidget(divider)

        # Account type
        account_type = QLabel(f"Type: {account.account_type}")
        account_type.setStyleSheet("font-size: 12px;")
        vl.addWidget(account_type)

        # Current Balance label
        balance_title = QLabel("Current Balance")
        balance_title.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 3px;")
        vl.addWidget(balance_title)

        # Balance
        ledger_entries = self.db.fetch_ledger_items(account.id)
        balance = 0
        for entry in ledger_entries:
            balance += entry.amount
        balance_label = QLabel(f"${balance:,.2f}")
        balance_font = QFont()
        balance_font.setPointSize(16)
        balance_font.setBold(True)
        balance_label.setFont(balance_font)
        balance_label.setStyleSheet("color: #27ae60; margin: 2px 0 5px 0;")
        vl.addWidget(balance_label)
        
        # Ledger entry count
        entry_count = QLabel(f"{len(ledger_entries)} ledger entries")
        entry_count.setStyleSheet("font-size: 11px;")
        vl.addWidget(entry_count)

        vl.addStretch(1)

        # View button
        edit_button = QPushButton("View Details")
        edit_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #546e7a;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        edit_button.clicked.connect(
            lambda button_clicked, a=account: self.select_account(a)
        )
        vl.addWidget(edit_button)

        widget.setLayout(vl)
        widget.show()

        return widget

    def select_account(self, account):
        if self.account_widget is not None:
            self.removeWidget(self.account_widget)
        self.account_widget = QWidget()
        vl = QVBoxLayout()
        vl.setSpacing(20)
        vl.setContentsMargins(20, 20, 20, 20)

        # Header section with back button and title
        header_container = QWidget()
        header_container.setStyleSheet("padding: 15px;")
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        
        # Back button row
        back_row = QHBoxLayout()
        back_button = QPushButton("Back to Accounts")
        back_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #546e7a;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        back_button.clicked.connect(lambda: self.setCurrentIndex(0))
        back_row.addWidget(back_button)
        back_row.addStretch(1)
        header_layout.addLayout(back_row)
        
        # Account icon and name
        account_icons = {
            "Checking": "[C]",
            "Savings": "[S]",
            "Credit Card": "[CC]"
        }
        icon = account_icons.get(account.account_type, "[A]")
        
        title_row = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(28)
        icon_label.setFont(icon_font)
        title_row.addWidget(icon_label)
        
        account_title = QLabel(account.name)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        account_title.setFont(title_font)
        title_row.addWidget(account_title)
        title_row.addStretch(1)
        header_layout.addLayout(title_row)
        
        header_container.setLayout(header_layout)
        vl.addWidget(header_container)

        # Account info section
        info_container = QWidget()
        info_container.setStyleSheet("padding: 20px;")
        info_layout = QHBoxLayout()
        info_layout.setSpacing(30)
        
        # Type column
        type_col = QVBoxLayout()
        type_label = QLabel("Account Type")
        type_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        type_col.addWidget(type_label)
        type_value = QLabel(account.account_type)
        type_value_font = QFont()
        type_value_font.setPointSize(14)
        type_value.setFont(type_value_font)
        type_col.addWidget(type_value)
        info_layout.addLayout(type_col)
        
        # Balance column
        ledger_items: list[LedgerEntry] = self.db.fetch_ledger_items(account.id)
        balance = 0
        for entry in ledger_items:
            balance += entry.amount
        
        balance_col = QVBoxLayout()
        balance_title = QLabel("Current Balance")
        balance_title.setStyleSheet("font-size: 12px; font-weight: bold;")
        balance_col.addWidget(balance_title)
        balance_label = QLabel(f"${balance:,.2f}")
        balance_font = QFont()
        balance_font.setPointSize(18)
        balance_font.setBold(True)
        balance_label.setFont(balance_font)
        balance_label.setStyleSheet("color: #27ae60;")
        balance_col.addWidget(balance_label)
        info_layout.addLayout(balance_col)
        
        # Ledger entries column
        entries_col = QVBoxLayout()
        entries_title = QLabel("Ledger Entries")
        entries_title.setStyleSheet("font-size: 12px; font-weight: bold;")
        entries_col.addWidget(entries_title)
        entries_value = QLabel(str(len(ledger_items)))
        entries_value_font = QFont()
        entries_value_font.setPointSize(14)
        entries_value.setFont(entries_value_font)
        entries_col.addWidget(entries_value)
        info_layout.addLayout(entries_col)
        
        info_layout.addStretch(1)
        
        # Add Ledger Entry button
        add_ledger_entry_button = QPushButton("Add Ledger Entry")
        add_ledger_entry_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #546e7a;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        add_ledger_entry_button.clicked.connect(
            lambda: self.add_ledger_entry(account)
        )
        info_layout.addWidget(add_ledger_entry_button)
        
        info_container.setLayout(info_layout)
        vl.addWidget(info_container)

        # Ledger table section
        ledger_label = QLabel(f"Ledger Entries ({len(ledger_items)})")
        ledger_label_font = QFont()
        ledger_label_font.setPointSize(16)
        ledger_label_font.setBold(True)
        ledger_label.setFont(ledger_label_font)
        ledger_label.setStyleSheet("margin-top: 10px;")
        vl.addWidget(ledger_label)
        
        if ledger_items:
            ledger_table = QTableWidget()
            ledger_table.setColumnCount(10)
            ledger_table.setRowCount(len(ledger_items))
            ledger_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            # Style the table
            ledger_table.setStyleSheet("""
                QTableWidget {
                    border-radius: 8px;
                }
                QTableWidget::item {
                    padding: 8px;
                }
                QHeaderView::section {
                    padding: 10px;
                    font-weight: bold;
                }
            """)
            
            ledger_table.setHorizontalHeaderLabels(
                [
                    "ID",
                    "Name",
                    "Paid Date",
                    "Income Date",
                    "Type",
                    "Amount",
                    "Created",
                    "Updated",
                    "Edit",
                    "Delete",
                ]
            )
            idx = 0
            for ledger_item in ledger_items:
                ledger_table.setItem(idx, 0, QTableWidgetItem(str(ledger_item.id)))
                ledger_table.setItem(idx, 1, QTableWidgetItem(ledger_item.name))
                ledger_table.setItem(
                    idx, 2, QTableWidgetItem(ledger_item.paid_date.strftime("%Y-%m-%d"))
                )
                ledger_table.setItem(
                    idx, 3, QTableWidgetItem(ledger_item.income_date.strftime("%Y-%m-%d"))
                )
                ledger_table.setItem(idx, 4, QTableWidgetItem(ledger_item.type))
                ledger_table.setItem(
                    idx, 5, QTableWidgetItem("${:,.2f}".format(ledger_item.amount))
                )
                ledger_table.setItem(
                    idx, 6, QTableWidgetItem(ledger_item.created_at.strftime("%Y-%m-%d"))
                )
                ledger_table.setItem(
                    idx, 7, QTableWidgetItem(ledger_item.updated_at.strftime("%Y-%m-%d"))
                )
                
                # Add Edit button
                edit_button = QPushButton("Edit")
                edit_button.setStyleSheet("""
                    QPushButton {
                        padding: 6px 12px;
                        border: 1px solid #546e7a;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                """)
                edit_button.clicked.connect(
                    lambda checked=False, item=ledger_item, acc=account: self.edit_ledger_item(item, acc)
                )
                ledger_table.setCellWidget(idx, 8, edit_button)
                
                # Add Delete button
                delete_button = QPushButton("Delete")
                delete_button.setStyleSheet("""
                    QPushButton {
                        padding: 6px 12px;
                        border: 1px solid #546e7a;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                """)
                delete_button.clicked.connect(
                    lambda checked=False, item=ledger_item, acc=account: self._delete_ledger_item(item, None, acc)
                )
                ledger_table.setCellWidget(idx, 9, delete_button)
                
                # Set row height to accommodate buttons
                ledger_table.setRowHeight(idx, 45)
                idx += 1

            vl.addWidget(ledger_table)
        else:
            # No ledger entries message
            no_entries = QLabel(
                "No ledger entries yet.\n\n"
                "Ledger entries are individual transactions — payments, deposits, refunds.\n"
                "Click 'Add Ledger Entry' above, or mark items as paid from the Calendar."
            )
            no_entries.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_entries.setWordWrap(True)
            no_entries.setStyleSheet("font-size: 13px; padding: 40px;")
            vl.addWidget(no_entries)

        self.account_widget.setLayout(vl)
        self.account_widget.show()

        self.addWidget(self.account_widget)
        self.setCurrentIndex(2)

    def render_accounts(self):
        widget = QWidget()
        vl = QVBoxLayout()
        vl.setSpacing(20)
        vl.setContentsMargins(20, 20, 20, 20)

        # Title section
        title_container = QWidget()
        title_container.setStyleSheet("padding: 15px;")
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        accounts_title = QLabel("Accounts")
        accounts_title_font = QFont()
        accounts_title_font.setPointSize(18)
        accounts_title_font.setBold(True)
        accounts_title.setFont(accounts_title_font)
        title_layout.addWidget(accounts_title)
        title_layout.addWidget(HelpIcon(HELP_TEXTS["accounts"]))
        title_layout.addStretch(1)
        
        # Add Account button in title
        createButton = QPushButton("Add Account")
        createButton.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #546e7a;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        createButton.clicked.connect(lambda: self.setCurrentIndex(1))
        title_layout.addWidget(createButton)
        
        title_container.setLayout(title_layout)
        vl.addWidget(title_container)

        # Accounts grid
        self.accounts = self.db.fetch_accounts(self.selected_profile.id)
        
        if self.accounts:
            accounts_container = QWidget()
            accounts_layout = QHBoxLayout()
            accounts_layout.setSpacing(20)
            accounts_layout.addStretch(1)
            
            for account in self.accounts:
                account_widget = self.render_account(account)
                accounts_layout.addWidget(account_widget)
            
            accounts_layout.addStretch(1)
            accounts_container.setLayout(accounts_layout)
            vl.addWidget(accounts_container)
        else:
            # No accounts message
            no_accounts_container = QWidget()
            no_accounts_vl = QVBoxLayout()
            no_accounts_vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_accounts_title = QLabel("No accounts yet")
            no_accounts_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            no_accounts_title.setFont(title_font)
            no_accounts_vl.addWidget(no_accounts_title)
            no_accounts_desc = QLabel(
                "Accounts represent your bank accounts — checking, savings, credit cards.\n"
                "Each account has a ledger that tracks transactions.\n\n"
                "Click 'Add Account' above to create your first one."
            )
            no_accounts_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_accounts_desc.setWordWrap(True)
            no_accounts_desc.setStyleSheet("font-size: 13px; padding: 20px;")
            no_accounts_vl.addWidget(no_accounts_desc)
            no_accounts_container.setLayout(no_accounts_vl)
            vl.addWidget(no_accounts_container)

        vl.addStretch(1)

        widget.setLayout(vl)
        widget.show()

        self.addWidget(widget)

    def render_create_account(self):
        widget = QWidget()
        vl = QVBoxLayout()
        vl.setSpacing(20)
        vl.setContentsMargins(20, 20, 20, 20)

        # Header Section
        header_container = QWidget()
        header_container.setStyleSheet("padding: 20px;")
        header_layout = QVBoxLayout()
        header_layout.setSpacing(15)
        
        # Back button
        back_button = QPushButton("Back to Accounts")
        back_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #546e7a;
                border-radius: 5px;
                font-size: 12px;
                text-align: left;
            }
        """)
        back_button.clicked.connect(lambda: self.setCurrentIndex(0))
        back_button.setMaximumWidth(180)
        header_layout.addWidget(back_button)
        
        # Title with icon
        title_row = QHBoxLayout()
        icon_label = QLabel("")
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        title_row.addWidget(icon_label)
        
        title_label = QLabel("New Account")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        header_layout.addLayout(title_row)
        
        # Form container with constrained width
        form_container = QWidget()
        form_container.setMaximumWidth(480)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(6)
        form_layout.setContentsMargins(0, 10, 0, 0)

        # Account Name field
        name_label = QLabel("Account Name")
        name_font = QFont()
        name_font.setPointSize(11)
        name_font.setBold(True)
        name_label.setFont(name_font)
        form_layout.addWidget(name_label)

        name = QLineEdit()
        name.setPlaceholderText("e.g., My Checking Account")
        name.setStyleSheet("padding: 10px; font-size: 14px;")
        name.setMinimumHeight(40)
        form_layout.addWidget(name)

        form_layout.addSpacing(12)

        # Account Type field
        type_label = QLabel("Account Type")
        type_font = QFont()
        type_font.setPointSize(11)
        type_font.setBold(True)
        type_label.setFont(type_font)
        form_layout.addWidget(type_label)

        account_type = QComboBox()
        account_type.addItems(["Checking", "Savings", "Credit Card"])
        account_type.setStyleSheet("padding: 8px; font-size: 14px;")
        account_type.setMinimumHeight(40)
        form_layout.addWidget(account_type)

        form_layout.addSpacing(12)

        # Balance field
        balance_label = QLabel("Starting Balance")
        balance_font = QFont()
        balance_font.setPointSize(11)
        balance_font.setBold(True)
        balance_label.setFont(balance_font)
        form_layout.addWidget(balance_label)

        balance = QLineEdit("0.00")
        balance.setStyleSheet("padding: 10px 10px 10px 28px; font-size: 14px;")
        balance.setMinimumHeight(40)
        # Overlay a $ label on the left inside the input
        dollar_overlay = QLabel("$", balance)
        dollar_overlay.setStyleSheet("font-size: 14px; font-weight: bold; padding-left: 10px; background: transparent; border: none;")
        dollar_overlay.move(2, 8)
        form_layout.addWidget(balance)

        form_layout.addSpacing(20)

        # Save button
        create_button = QPushButton("SAVE ACCOUNT")
        create_button.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                border: 1px solid #546e7a;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        create_button.setMinimumHeight(44)
        create_button.clicked.connect(
            lambda: self.create_account(
                name.text(), account_type.currentText(), balance.text()
            )
        )
        form_layout.addWidget(create_button)

        form_container.setLayout(form_layout)
        header_layout.addWidget(form_container)

        header_container.setLayout(header_layout)
        vl.addWidget(header_container)

        vl.addStretch(1)

        widget.setLayout(vl)
        widget.show()

        self.addWidget(widget)

    def edit_ledger_item(self, ledger_item: LedgerEntry, account: Account):
        """Open dialog to edit a ledger item."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Ledger Entry - {ledger_item.name}")
        dialog.setMinimumWidth(480)

        input_style = "padding: 10px; font-size: 14px;"
        input_height = 40
        label_font = QFont()
        label_font.setPointSize(11)
        label_font.setBold(True)
        btn_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"

        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(20, 20, 20, 16)

        def add_field_label(text):
            lbl = QLabel(text)
            lbl.setFont(label_font)
            layout.addWidget(lbl)

        # Name
        add_field_label("Name")
        name_input = QLineEdit(ledger_item.name)
        name_input.setStyleSheet(input_style)
        name_input.setMinimumHeight(input_height)
        layout.addWidget(name_input)
        layout.addSpacing(8)

        # Amount
        add_field_label("Amount")
        amount_input = QLineEdit(str(ledger_item.amount))
        amount_input.setStyleSheet(input_style)
        amount_input.setMinimumHeight(input_height)
        layout.addWidget(amount_input)
        layout.addSpacing(8)

        # Type
        add_field_label("Type")
        type_input = QComboBox()
        type_input.addItems(["Income", "Expense"])
        type_input.setCurrentText(ledger_item.type)
        type_input.setStyleSheet(input_style)
        type_input.setMinimumHeight(input_height)
        layout.addWidget(type_input)
        layout.addSpacing(8)

        # Paid Date
        add_field_label("Paid Date")
        paid_date_input = QDateEdit()
        paid_date_input.setCalendarPopup(True)
        paid_date_input.setDate(QDate.fromString(ledger_item.paid_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        paid_date_input.setStyleSheet(input_style)
        paid_date_input.setMinimumHeight(input_height)
        layout.addWidget(paid_date_input)
        layout.addSpacing(8)

        # Income Date
        add_field_label("Income Date")
        income_date_input = QDateEdit()
        income_date_input.setCalendarPopup(True)
        income_date_input.setDate(QDate.fromString(ledger_item.income_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        income_date_input.setStyleSheet(input_style)
        income_date_input.setMinimumHeight(input_height)
        layout.addWidget(income_date_input)
        layout.addSpacing(8)

        # Account selector
        add_field_label("Account")
        account_selector = QComboBox()
        accounts = self.db.fetch_accounts(self.selected_profile.id)
        for acc in accounts:
            account_selector.addItem(acc.name)
        current_account_name = next((a.name for a in accounts if a.id == ledger_item.account_id), account.name)
        account_selector.setCurrentText(current_account_name)
        account_selector.setStyleSheet(input_style)
        account_selector.setMinimumHeight(input_height)
        layout.addWidget(account_selector)

        layout.addSpacing(16)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        delete_button = QPushButton("Delete")
        delete_button.setStyleSheet(btn_style)
        delete_button.setMinimumHeight(40)
        delete_button.clicked.connect(
            lambda: self._delete_ledger_item(ledger_item, dialog, account)
        )
        button_layout.addWidget(delete_button)

        button_layout.addStretch(1)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(btn_style)
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setStyleSheet(btn_style)
        save_button.setMinimumHeight(40)
        save_button.clicked.connect(
            lambda: self._save_ledger_item(
                ledger_item.id,
                name_input.text(),
                paid_date_input.date().toString("yyyy-MM-dd"),
                income_date_input.date().toString("yyyy-MM-dd"),
                float(amount_input.text()),
                accounts[account_selector.currentIndex()].id,
                dialog,
                account
            )
        )
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec()
    
    def _save_ledger_item(self, ledger_id, name, paid_date, income_date, amount, account_id, dialog, original_account):
        """Save updated ledger item."""
        try:
            self.db.update_ledger_entry(ledger_id, name, paid_date, income_date, amount, account_id)
            QMessageBox.information(
                self,
                "Success",
                "Ledger entry updated successfully."
            )
            dialog.accept()
            # Refresh the account view
            self.select_account(original_account)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update ledger entry: {str(e)}"
            )
    
    def _delete_ledger_item(self, ledger_item, dialog, account):
        """Delete ledger item with confirmation."""
        reply = QMessageBox.question(
            self,
            "Delete Ledger Entry",
            f"Are you sure you want to delete ledger entry '{ledger_item.name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_ledger_entry(ledger_item.id)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Ledger entry '{ledger_item.name}' has been deleted."
                )
                if dialog:  # Only accept dialog if it exists
                    dialog.accept()
                # Refresh the account view
                self.select_account(account)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete ledger entry: {str(e)}"
                )

    def create_account(self, name, account_type, balance):
        try:
            self.db.create_account(self.selected_profile.id, name, account_type, balance)
            # Rebuild both views (accounts list + form) so the form is fresh
            while self.count() > 0:
                w = self.widget(0)
                self.removeWidget(w)
                w.deleteLater()
            self.render_accounts()
            self.render_create_account()
            self.setCurrentIndex(0)
            QMessageBox.information(
                self, "Success", f"Account '{name}' created successfully!"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to create account: {str(e)}"
            )
    
    def add_ledger_entry(self, account):
        """Show dialog to add a new ledger entry."""
        from datetime import date

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Ledger Entry")
        dialog.setMinimumWidth(480)

        input_style = "padding: 10px; font-size: 14px;"
        input_height = 40
        label_font = QFont()
        label_font.setPointSize(11)
        label_font.setBold(True)
        btn_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"

        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(20, 20, 20, 16)

        # Header
        header_label = QLabel("Add Ledger Entry")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        desc_label = QLabel(f"Add a transaction to {account.name}")
        desc_label.setStyleSheet("font-size: 13px; color: #90a4ae;")
        layout.addWidget(desc_label)
        layout.addSpacing(12)

        def add_field_label(text):
            lbl = QLabel(text)
            lbl.setFont(label_font)
            layout.addWidget(lbl)

        # Name
        add_field_label("Name")
        name_input = QLineEdit()
        name_input.setPlaceholderText("Transaction name")
        name_input.setStyleSheet(input_style)
        name_input.setMinimumHeight(input_height)
        layout.addWidget(name_input)
        layout.addSpacing(8)

        # Amount
        add_field_label("Amount")
        amount_input = QLineEdit('0.00')
        amount_input.setStyleSheet(input_style)
        amount_input.setMinimumHeight(input_height)
        layout.addWidget(amount_input)
        layout.addSpacing(8)

        # Type
        add_field_label("Type")
        type_combo = QComboBox()
        type_combo.addItems(["Income", "Expense"])
        type_combo.setStyleSheet(input_style)
        type_combo.setMinimumHeight(input_height)
        layout.addWidget(type_combo)
        layout.addSpacing(8)

        # Paid Date
        add_field_label("Paid Date")
        paid_date_input = QDateEdit(date.today())
        paid_date_input.setCalendarPopup(True)
        paid_date_input.setStyleSheet(input_style)
        paid_date_input.setMinimumHeight(input_height)
        layout.addWidget(paid_date_input)
        layout.addSpacing(8)

        # Income Date
        add_field_label("Income Date")
        income_date_input = QDateEdit(date.today())
        income_date_input.setCalendarPopup(True)
        income_date_input.setStyleSheet(input_style)
        income_date_input.setMinimumHeight(input_height)
        layout.addWidget(income_date_input)

        layout.addSpacing(16)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch(1)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(btn_style)
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)

        save_button = QPushButton("Save Entry")
        save_button.setStyleSheet(btn_style)
        save_button.setMinimumHeight(40)
        save_button.clicked.connect(
            lambda: self._save_new_ledger_entry(
                account,
                name_input.text(),
                float(amount_input.text() or 0),
                type_combo.currentText(),
                paid_date_input.date().toPyDate(),
                income_date_input.date().toPyDate(),
                dialog
            )
        )
        buttons_layout.addWidget(save_button)

        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        dialog.exec()
    
    def _save_new_ledger_entry(self, account, name, amount, entry_type, paid_date, income_date, dialog):
        """Save a new ledger entry."""
        try:
            ledger_entry = self.db.create_ledger_entry(
                name=name,
                date=paid_date,
                incomeDate=income_date,
                type=entry_type,
                amount=-amount if entry_type == "Expense" else amount,
                accountId=account.id
            )
            
            QMessageBox.information(
                self,
                "Success",
                f"Ledger entry '{name}' created successfully!"
            )
            
            dialog.accept()
            # Refresh the account view
            self.select_account(account)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create ledger entry: {str(e)}")
