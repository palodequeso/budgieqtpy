import locale
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
)
from PyQt6.QtGui import QPalette, QColor
from database.account import Account
from database.database import Database
from database.ledger_entry import LedgerEntry
from database.profile import Profile

ACCOUNT_COLORS = {
    "Checking": "#b2dfdb",
    "Savings": "#b3e5fc",
    "Credit Card": "#ffcdd2",
}


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
        widget.setPalette(QPalette(QColor(ACCOUNT_COLORS[account.account_type])))
        widget.setAutoFillBackground(True)

        widget.setContentsMargins(10, 10, 10, 10)
        widget.setFixedWidth(250)
        widget.setFixedHeight(200)

        vl = QVBoxLayout()

        name = QLabel("Name: " + account.name)
        vl.addWidget(name)

        account_type = QLabel("Type: " + account.account_type)
        vl.addWidget(account_type)

        ledger_entries = self.db.fetch_ledger_items(account.id)
        balance = 0
        for entry in ledger_entries:
            balance += entry.amount
        balance_label = QLabel("Balance: ${:,.2f}".format(balance))
        vl.addWidget(balance_label)

        created_at = QLabel("Created: " + account.created_at.strftime("%Y-%m-%d"))
        vl.addWidget(created_at)

        updated_at = QLabel("Updated: " + account.updated_at.strftime("%Y-%m-%d"))
        vl.addWidget(updated_at)

        edit_button = QPushButton("View")
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

        bhl = QHBoxLayout()
        bhl.addStretch(1)

        back_button = QPushButton("Back")
        bhl.addWidget(back_button)
        back_button.clicked.connect(lambda: self.setCurrentIndex(0))

        vl.addLayout(bhl)

        name = QLabel("Name: " + account.name)
        vl.addWidget(name)

        account_type = QLabel("Type: " + account.account_type)
        vl.addWidget(account_type)

        ledger_items: list[LedgerEntry] = self.db.fetch_ledger_items(account.id)
        balance = 0
        for entry in ledger_items:
            balance += entry.amount
        balance_label = QLabel("Balance: ${:,.2f}".format(account.balance))
        vl.addWidget(balance_label)

        created_at = QLabel("Created: " + account.created_at.strftime("%Y-%m-%d"))
        vl.addWidget(created_at)

        last_row_hl = QHBoxLayout()
        updated_at = QLabel("Updated: " + account.updated_at.strftime("%Y-%m-%d"))
        last_row_hl.addWidget(updated_at)
        last_row_hl.addStretch(1)

        add_ledger_entry_button = QPushButton("Add Ledger Entry")
        last_row_hl.addWidget(add_ledger_entry_button)
        # add_ledger_entry_button.clicked.connect(
        #     lambda: self.setCurrentIndex(2)
        # )

        vl.addLayout(last_row_hl)

        ledger_table = QTableWidget()
        ledger_table.setColumnCount(8)
        ledger_table.setRowCount(len(ledger_items))
        ledger_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ledger_table.horizontalHeader().setStretchLastSection(True)

        ledger_table.setHorizontalHeaderLabels(
            [
                "Id",
                "Name",
                "Date",
                "Income Date",
                "Type",
                "Amount",
                "Created",
                "Updated",
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
            idx += 1

        vl.addWidget(ledger_table)

        self.account_widget.setLayout(vl)
        self.account_widget.show()

        self.addWidget(self.account_widget)
        self.setCurrentIndex(2)

    def render_accounts(self):
        widget = QWidget()
        vl = QVBoxLayout()

        l = QHBoxLayout()

        toolsRow = QHBoxLayout()
        toolsRow.addStretch(1)
        createButton = QPushButton("Create")
        createButton.clicked.connect(lambda: self.setCurrentIndex(1))
        toolsRow.addWidget(createButton)
        vl.addLayout(toolsRow)

        self.accounts = self.db.fetch_accounts(self.selected_profile.id)
        for account in self.accounts:
            account_widget = self.render_account(account)
            l.addWidget(account_widget)

        l.addStretch(1)

        vl.addLayout(l)

        vl.addStretch(1)

        widget.setLayout(vl)
        widget.show()

        self.addWidget(widget)

    def render_create_account(self):
        widget = QWidget()
        vl = QVBoxLayout()

        # vl.addStretch(1)

        name = QLineEdit()
        name.setPlaceholderText("Name")
        vl.addWidget(name)

        account_type = QComboBox()
        account_type.addItems(["Checking", "Savings", "Credit Card"])
        vl.addWidget(account_type)

        balance = QLineEdit()
        balance.setPlaceholderText("Balance")
        vl.addWidget(balance)

        bhl = QHBoxLayout()

        create_button = QPushButton("Create")
        bhl.addWidget(create_button)

        cancel_button = QPushButton("Cancel")
        bhl.addWidget(cancel_button)

        vl.addLayout(bhl)

        create_button.clicked.connect(
            lambda: self.create_account(
                name.text(), account_type.currentText(), balance.text()
            )
        )
        cancel_button.clicked.connect(lambda: self.setCurrentIndex(0))

        vl.addStretch(1)

        hl = QHBoxLayout()
        hl.addStretch(1)
        hl.addLayout(vl)
        hl.addStretch(1)

        widget.setLayout(hl)
        widget.show()

        self.addWidget(widget)

    def create_account(self, name, account_type, balance):
        self.db.create_account(self.selected_profile.id, name, account_type, balance)
        self.setCurrentIndex(0)
