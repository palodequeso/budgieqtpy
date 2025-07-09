from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QStackedWidget,
)
from PyQt6.QtCore import QDate

from database import BudgetItemPeriod
from database.budget_group import BudgetGroup
from database.budget_item import BudgetItem
from database.database import Database
from database.profile import Profile


class Budget(QStackedWidget):
    db: Database = None
    selected_profile: Profile = None
    budget_groups: list[BudgetGroup] = None
    budget_items: list[BudgetItem] = None

    def __init__(self, db, selected_profile):
        super().__init__()
        self.db = db
        self.selected_profile = selected_profile
        self.budget_groups = []
        self.budget_items = []

        self.render_budget()
        self.render_create_budget_item()

    def render_budget(self):
        widget = QWidget()
        vl = QVBoxLayout()

        toolsRow = QHBoxLayout()
        toolsRow.addStretch(1)
        createButton = QPushButton("Create")
        createButton.clicked.connect(lambda: self.setCurrentIndex(1))
        toolsRow.addWidget(createButton)
        vl.addLayout(toolsRow)

        table = QTableWidget()
        self.budget_groups = self.db.fetch_budget_groups(self.selected_profile.id)
        self.budget_items = self.db.fetch_budget_items(self.selected_profile.id)
        table.setColumnCount(9)
        table.setRowCount(len(self.budget_items))
        table.setHorizontalHeaderLabels(
            [
                "Name",
                "Type",
                "Amount",
                "Created At",
                "Updated At",
                "Start Date",
                "End Date",
                "Group",
                "Periods",
            ]
        )
        table.horizontalHeader().setStretchLastSection(True)

        idx = 0
        for budget_items in self.budget_items:
            table.setItem(idx, 0, QTableWidgetItem(budget_items.name))
            table.setItem(idx, 1, QTableWidgetItem(budget_items.type))
            table.setItem(idx, 2, QTableWidgetItem(str(budget_items.amount)))
            table.setItem(
                idx, 3, QTableWidgetItem(budget_items.created_at.strftime("%Y-%m-%d"))
            )
            table.setItem(
                idx, 4, QTableWidgetItem(budget_items.updated_at.strftime("%Y-%m-%d"))
            )
            table.setItem(
                idx, 5, QTableWidgetItem(budget_items.start_date.strftime("%Y-%m-%d"))
            )
            table.setItem(
                idx, 6, QTableWidgetItem(budget_items.end_date.strftime("%Y-%m-%d"))
            )
            table.setItem(idx, 7, QTableWidgetItem(str(budget_items.budget_group_id)))

            periodsStr = ""
            for period in budget_items.periods:
                periodsStr += period.type + ": " + str(period.value)
                if period.business_day != "None":
                    periodsStr += " (" + period.business_day + ")\t"
            table.setItem(idx, 8, QTableWidgetItem(periodsStr))
            idx += 1
        vl.addWidget(table)

        # vl.addStretch(1)

        widget.setLayout(vl)
        widget.show()

        if self.count() > 0:
            self.setCurrentIndex(0)
            self.setCurrentWidget(widget)
        else:
            self.addWidget(widget)

    def render_create_budget_item(self):
        widget = QWidget()

        vl = QVBoxLayout()

        name = QLineEdit()
        name.setPlaceholderText("Name")
        vl.addWidget(name)

        type = QComboBox()
        type.addItems(["Income", "Expense"])
        vl.addWidget(type)

        amount = QLineEdit()
        amount.setPlaceholderText("Amount")
        vl.addWidget(amount)

        ghl = QHBoxLayout()
        new_group = QLineEdit()
        new_group.setPlaceholderText("New Group")
        ghl.addWidget(new_group)

        group_combo = QComboBox()
        new_group_create = QPushButton("Add Group")
        new_group_create.clicked.connect(
            lambda: self.add_budget_group(group_combo, new_group.text())
        )
        ghl.addWidget(new_group_create)

        vl.addLayout(ghl)

        existing_groups = self.db.fetch_budget_groups(self.selected_profile.id)
        group_combo.addItems([group.name for group in existing_groups])
        vl.addWidget(group_combo)

        dhl = QHBoxLayout()
        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setDate(QDate.currentDate())
        # start_date.setPlaceholderText("Start Date")
        start_date.setDate(QDate.currentDate())
        dhl.addWidget(start_date)

        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        # end_date.setPlaceholderText("End Date")
        dhl.addWidget(end_date)

        vl.addLayout(dhl)

        period_layout = QVBoxLayout()

        add_period_button = QPushButton("Add Period")
        add_period_button.clicked.connect(
            lambda: self.add_budget_period(period_layout, True)
        )
        vl.addWidget(add_period_button)
        self.add_budget_period(period_layout)

        vl.addLayout(period_layout)

        button_hl = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        create_button = QPushButton("Create")
        button_hl.addWidget(cancel_button)
        button_hl.addWidget(create_button)

        vl.addLayout(button_hl)

        cancel_button.clicked.connect(lambda: self.setCurrentIndex(0))
        create_button.clicked.connect(
            lambda: self.create_budget_item(
                name.text(),
                type.currentText(),
                amount.text(),
                group_combo.currentText(),
                start_date.date().toString("yyyy-MM-dd"),
                end_date.date().toString("yyyy-MM-dd"),
                self.periods_from_layout(period_layout),
            )
        )

        vl.addStretch(1)

        hl = QHBoxLayout()
        hl.addStretch(1)
        hl.addLayout(vl)
        hl.addStretch(1)

        widget.setLayout(hl)
        self.addWidget(widget)

    def add_budget_group(self, combobox, name):
        self.db.create_budget_group(self.selected_profile.id, name)
        combobox.addItem(name)

    def add_budget_period(self, layout, removable=False):
        hl = QHBoxLayout()

        budget_type = QComboBox()
        budget_type.addItems(
            ["Monthly", "Weekly", "Biweekly", "Daily", "Business Days"]
        )  # , "Yearly"])
        hl.addWidget(budget_type)

        budget_value = QComboBox()
        hl.addWidget(budget_value)

        self.update_budget_value(budget_value, budget_type.currentText())
        budget_type.currentTextChanged.connect(
            lambda: self.update_budget_value(budget_value, budget_type.currentText())
        )

        business_day = QComboBox()
        business_day.addItems(["None", "Previous", "Next"])
        hl.addWidget(business_day)

        remove_button = QPushButton("Remove")
        if removable:
            remove_button.clicked.connect(lambda: self.remove_budget_period(hl, layout))
        else:
            remove_button.setEnabled(False)
        hl.addWidget(remove_button)

        layout.addLayout(hl)

    def periods_from_layout(self, layout) -> list[BudgetItemPeriod]:
        periods = []
        for i in range(layout.count()):
            layout_item = layout.itemAt(i)
            budget_type = layout_item.layout().itemAt(0).widget()
            budget_value = layout_item.layout().itemAt(1).widget()
            business_day = layout_item.layout().itemAt(2).widget()
            periods.append(
                BudgetItemPeriod(
                    budget_type.currentText(),
                    budget_value.currentText(),
                    business_day.currentText(),
                    None,
                    0,
                    None,
                    None,
                )
            )
        return periods

    def remove_budget_period(self, layout, parent):
        parent.removeItem(layout)

    def update_budget_value(self, combobox, value):
        combobox.setEnabled(True)
        if value == "Monthly":
            combobox.clear()
            combobox.addItems(
                [
                    "1st",
                    "2nd",
                    "3rd",
                    "4th",
                    "5th",
                    "6th",
                    "7th",
                    "8th",
                    "9th",
                    "10th",
                    "11th",
                    "12th",
                    "13th",
                    "14th",
                    "15th",
                    "16th",
                    "17th",
                    "18th",
                    "19th",
                    "20th",
                    "21st",
                    "22nd",
                    "23rd",
                    "24th",
                    "25th",
                    "26th",
                    "27th",
                    "28th",
                    "29th",
                    "30th",
                    "31st",
                    "Last",
                ]
            )
        elif value == "Weekly" or value == "Biweekly":
            combobox.clear()
            combobox.addItems(
                [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]
            )
        elif value == "Business Days":
            combobox.clear()
            combobox.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        elif value == "Daily":
            combobox.clear()
            combobox.setEnabled(False)

    def create_budget_item(
        self, name, type, amount, group, start_date, end_date, periods
    ):
        self.db.create_budget_item(
            self.selected_profile.id,
            name,
            type,
            amount,
            group,
            start_date,
            end_date,
            periods,
        )
        self.render_budget()
