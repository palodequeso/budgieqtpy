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
    QMessageBox,
    QLabel,
    QHeaderView,
    QScrollArea,
    QCheckBox,
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont

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
    editing_budget_item: BudgetItem = None

    def __init__(self, db, selected_profile):
        super().__init__()
        self.db = db
        self.selected_profile = selected_profile
        self.budget_groups = []
        self.budget_items = []
        self.editing_budget_item = None

        self.render_budget()
        self.render_budget_item_form()

    def render_budget(self):
        widget = QWidget()
        vl = QVBoxLayout()
        vl.setSpacing(20)
        vl.setContentsMargins(20, 20, 20, 20)

        # Title section
        title_container = QWidget()
        title_container.setStyleSheet("border-radius: 8px; padding: 15px;")
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        budget_title = QLabel("💰 Budget Items")
        budget_title_font = QFont()
        budget_title_font.setPointSize(18)
        budget_title_font.setBold(True)
        budget_title.setFont(budget_title_font)
        title_layout.addWidget(budget_title)
        title_layout.addStretch(1)
        
        # Add Budget Item button in title
        createButton = QPushButton("➕ Add Budget Item")
        createButton.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        createButton.clicked.connect(lambda: self.setCurrentIndex(1))
        title_layout.addWidget(createButton)
        
        title_container.setLayout(title_layout)
        vl.addWidget(title_container)

        # Budget items table
        self.budget_groups = self.db.fetch_budget_groups(self.selected_profile.id)
        self.budget_items = self.db.fetch_budget_items(self.selected_profile.id)
        
        if self.budget_items:
            # Table label
            table_label = QLabel(f"📋 {len(self.budget_items)} Budget Items")
            table_label_font = QFont()
            table_label_font.setPointSize(14)
            table_label_font.setBold(True)
            table_label.setFont(table_label_font)
            vl.addWidget(table_label)
            
            table = QTableWidget()
            table.setColumnCount(10)
            table.setRowCount(len(self.budget_items))
            # Style the table
            table.setStyleSheet("""
                QTableWidget {
                    border: 2px solid;
                    border-radius: 8px;
                }
                QTableWidget::item {
                    padding: 8px;
                }
                QTableWidget::item:selected {
                    background-color: #1976d2;
                }
                QHeaderView::section {
                    padding: 10px;
                    border: none;
                    font-weight: bold;
                }
            """)
            
            table.setHorizontalHeaderLabels(
                [
                    "Name",
                    "Type",
                    "Amount",
                    "Start Date",
                    "End Date",
                    "Group",
                    "Periods",
                    "Created",
                    "Updated",
                    "Actions",
                ]
            )
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            table.horizontalHeader().setStretchLastSection(True)

            idx = 0
            for budget_items in self.budget_items:
                # Name with emoji based on type
                name_item = QTableWidgetItem(f"{'💵' if budget_items.type == 'Income' else '💸'} {budget_items.name}")
                table.setItem(idx, 0, name_item)
                
                # Type with color
                type_item = QTableWidgetItem(budget_items.type)
                table.setItem(idx, 1, type_item)
                
                # Amount formatted as currency
                amount_item = QTableWidgetItem(f"${float(budget_items.amount):,.2f}")
                table.setItem(idx, 2, amount_item)
                
                table.setItem(
                    idx, 3, QTableWidgetItem(budget_items.start_date.strftime("%Y-%m-%d"))
                )
                table.setItem(
                    idx, 4, QTableWidgetItem(budget_items.end_date.strftime("%Y-%m-%d"))
                )
                
                # Group name instead of ID
                group = next((g for g in self.budget_groups if g.id == budget_items.budget_group_id), None)
                group_name = group.name if group else "None"
                table.setItem(idx, 5, QTableWidgetItem(group_name))

                # Periods formatted nicely
                periodsStr = ""
                for period in budget_items.periods:
                    periodsStr += period.type + ": " + str(period.value)
                    if period.business_day != "None":
                        periodsStr += " (" + period.business_day + ")\n"
                table.setItem(idx, 6, QTableWidgetItem(periodsStr.strip()))
                
                table.setItem(
                    idx, 7, QTableWidgetItem(budget_items.created_at.strftime("%Y-%m-%d"))
                )
                table.setItem(
                    idx, 8, QTableWidgetItem(budget_items.updated_at.strftime("%Y-%m-%d"))
                )
                
                # Add Edit and Delete buttons
                button_widget = QWidget()
                button_layout = QHBoxLayout()
                button_layout.setContentsMargins(2, 2, 2, 2)
                button_layout.setSpacing(5)
                
                edit_button = QPushButton("✏️ Edit")
                edit_button.setStyleSheet("""
                    QPushButton {
                        background-color: #1976d2;
                        color: white;
                        padding: 6px 12px;
                        border: none;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #1565c0;
                    }
                """)
                edit_button.clicked.connect(
                    lambda checked=False, item=budget_items: self.edit_budget_item(item)
                )
                button_layout.addWidget(edit_button)
                
                delete_button = QPushButton("🗑️ Delete")
                delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: #d32f2f;
                        color: white;
                        padding: 6px 12px;
                        border: none;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #c62828;
                    }
                """)
                delete_button.clicked.connect(
                    lambda checked=False, item=budget_items: self.delete_budget_item(item)
                )
                button_layout.addWidget(delete_button)
                
                button_widget.setLayout(button_layout)
                table.setCellWidget(idx, 9, button_widget)
                
                # Set row height to accommodate buttons
                table.setRowHeight(idx, 45)
                idx += 1
            vl.addWidget(table)
        else:
            # No budget items message
            no_items_label = QLabel("No budget items yet. Click 'Add Budget Item' to create one.")
            no_items_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_items_label.setStyleSheet("font-size: 14px; padding: 40px; border-radius: 8px;")
            vl.addWidget(no_items_label)

        # vl.addStretch(1)

        widget.setLayout(vl)
        widget.show()

        if self.count() > 0:
            self.setCurrentIndex(0)
            self.setCurrentWidget(widget)
        else:
            self.addWidget(widget)

    def edit_budget_item(self, budget_item: BudgetItem):
        """Load budget item into form for editing."""
        self.editing_budget_item = budget_item
        self.render_budget_item_form(budget_item)
        self.setCurrentIndex(1)

    def render_budget_item_form(self, budget_item: BudgetItem = None):
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget inside scroll
        content_widget = QWidget()
        vl = QVBoxLayout()
        vl.setSpacing(10)
        vl.setContentsMargins(8, 8, 8, 8)
        
        # Header section
        header_container = QWidget()
        header_container.setStyleSheet("border-radius: 6px; padding: 10px;")
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        
        # Back button
        back_row = QHBoxLayout()
        back_button = QPushButton("⬅️ Back to Budget")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #546e7a;
                color: white;
                padding: 6px 14px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #607d8b;
            }
        """)
        back_button.clicked.connect(lambda: self.cancel_edit())
        back_row.addWidget(back_button)
        back_row.addStretch(1)
        header_layout.addLayout(back_row)
        
        # Title
        title = QLabel(f"✏️ {'Edit' if budget_item else 'Create'} Budget Item")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        # Description
        desc = QLabel("Budget items are recurring income or expenses that appear in your calendar. Set up when and how often they occur.")
        desc.setStyleSheet("font-size: 12px;")
        desc.setWordWrap(True)
        header_layout.addWidget(desc)
        
        header_container.setLayout(header_layout)
        vl.addWidget(header_container)

        # Two-column layout for main sections
        two_col_layout = QHBoxLayout()
        two_col_layout.setSpacing(10)
        
        # LEFT COLUMN - Basic Info Section
        basic_container = QWidget()
        basic_container.setStyleSheet("border-radius: 6px; padding: 10px;")
        basic_layout = QVBoxLayout()
        basic_layout.setSpacing(8)
        
        section_title = QLabel("📋 Basic Information")
        section_title_font = QFont()
        section_title_font.setPointSize(14)
        section_title_font.setBold(True)
        section_title.setFont(section_title_font)
        basic_layout.addWidget(section_title)
        
        # Name field
        name_label = QLabel("Item Name")
        name_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        basic_layout.addWidget(name_label)
        
        name = QLineEdit()
        name.setPlaceholderText("e.g., Rent, Salary, Groceries")
        name.setText(budget_item.name if budget_item else "")
        basic_layout.addWidget(name)

        # Type field
        type_label = QLabel("Type")
        type_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        basic_layout.addWidget(type_label)
        
        type_help = QLabel("Is this money coming in (Income) or going out (Expense)?")
        type_help.setStyleSheet("font-size: 10px; font-style: italic;")
        basic_layout.addWidget(type_help)
        
        type = QComboBox()
        type.addItems(["Income", "Expense"])
        if budget_item:
            type.setCurrentText(budget_item.type)
        basic_layout.addWidget(type)

        # Amount field
        amount_label = QLabel("Amount")
        amount_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        basic_layout.addWidget(amount_label)
        
        amount = QLineEdit()
        amount.setPlaceholderText("0.00")
        amount.setText(str(budget_item.amount) if budget_item else "")
        basic_layout.addWidget(amount)
        
        basic_layout.addStretch(1)
        basic_container.setLayout(basic_layout)
        two_col_layout.addWidget(basic_container)

        # RIGHT COLUMN - Contains Categorization and Date Range
        right_column = QVBoxLayout()
        right_column.setSpacing(10)
        
        # Group Section
        group_container = QWidget()
        group_container.setStyleSheet("border-radius: 6px; padding: 10px;")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(8)
        
        group_section_title = QLabel("📊 Categorization (Optional)")
        group_section_title_font = QFont()
        group_section_title_font.setPointSize(14)
        group_section_title_font.setBold(True)
        group_section_title.setFont(group_section_title_font)
        group_layout.addWidget(group_section_title)
        
        group_help = QLabel("Group similar items together (e.g., 'Housing', 'Transportation', 'Entertainment')")
        group_help.setStyleSheet("font-size: 10px; font-style: italic;")
        group_layout.addWidget(group_help)
        
        existing_groups = self.db.fetch_budget_groups(self.selected_profile.id)
        group_combo = QComboBox()
        group_combo.addItems([group.name for group in existing_groups])
        if budget_item and budget_item.budget_group_id:
            group = next((g for g in existing_groups if g.id == budget_item.budget_group_id), None)
            if group:
                group_combo.setCurrentText(group.name)
        group_layout.addWidget(group_combo)
        
        # Create new group
        new_group_row = QHBoxLayout()
        new_group = QLineEdit()
        new_group.setPlaceholderText("Create new group...")
        new_group_row.addWidget(new_group)

        new_group_create = QPushButton("➕ Add Group")
        new_group_create.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        new_group_create.clicked.connect(
            lambda: self.add_budget_group(group_combo, new_group.text())
        )
        new_group_row.addWidget(new_group_create)
        group_layout.addLayout(new_group_row)
        
        group_container.setLayout(group_layout)
        right_column.addWidget(group_container)

        # Date Range Section
        date_container = QWidget()
        date_container.setStyleSheet("border-radius: 6px; padding: 10px;")
        date_layout = QVBoxLayout()
        date_layout.setSpacing(8)
        
        date_section_title = QLabel("📅 Active Period")
        date_section_title_font = QFont()
        date_section_title_font.setPointSize(14)
        date_section_title_font.setBold(True)
        date_section_title.setFont(date_section_title_font)
        date_layout.addWidget(date_section_title)
        
        date_help = QLabel("When should this item be active? For ongoing items, check 'No end date'.")
        date_help.setStyleSheet("font-size: 10px; font-style: italic;")
        date_layout.addWidget(date_help)
        
        # Start Date
        start_label = QLabel("Start Date")
        start_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        date_layout.addWidget(start_label)
        
        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        if budget_item:
            start_date.setDate(QDate.fromString(budget_item.start_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        else:
            start_date.setDate(QDate.currentDate())
        date_layout.addWidget(start_date)
        
        # End Date with checkbox
        end_date_row = QHBoxLayout()
        end_date_row.setSpacing(10)
        
        end_label = QLabel("End Date")
        end_label.setStyleSheet("color: #333; font-size: 11px; font-weight: bold;")
        date_layout.addWidget(end_label)
        
        # Checkbox for "no end date"
        no_end_date_checkbox = QCheckBox("No end date (ongoing)")
        no_end_date_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
            }
        """)
        
        # Set default: check if editing and has far future date, or if creating new
        if budget_item:
            # Check if end date is far in the future (e.g., year > 2100)
            has_end_date = budget_item.end_date.year < 2100
            no_end_date_checkbox.setChecked(not has_end_date)
        else:
            # Default to no end date for new items
            no_end_date_checkbox.setChecked(True)
        
        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        if budget_item and budget_item.end_date.year < 2100:
            end_date.setDate(QDate.fromString(budget_item.end_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        else:
            # Set to one year from now as default
            end_date.setDate(QDate.currentDate().addYears(1))
        
        # Connect checkbox to enable/disable end date
        def toggle_end_date(checked):
            end_date.setEnabled(not checked)
        
        no_end_date_checkbox.toggled.connect(toggle_end_date)
        # Set initial state
        end_date.setEnabled(not no_end_date_checkbox.isChecked())
        
        date_layout.addWidget(no_end_date_checkbox)
        date_layout.addWidget(end_date)
        
        date_container.setLayout(date_layout)
        right_column.addWidget(date_container)
        right_column.addStretch(1)
        
        # Add right column to two-column layout
        two_col_layout.addLayout(right_column)
        
        # Add two-column layout to main layout
        vl.addLayout(two_col_layout)

        # Periods Section (Full Width)
        period_container = QWidget()
        period_container.setStyleSheet("border-radius: 6px; padding: 10px;")
        period_outer_layout = QVBoxLayout()
        period_outer_layout.setSpacing(8)
        
        period_section_title = QLabel("🔁 Recurrence Schedule")
        period_section_title_font = QFont()
        period_section_title_font.setPointSize(14)
        period_section_title_font.setBold(True)
        period_section_title.setFont(period_section_title_font)
        period_outer_layout.addWidget(period_section_title)
        
        period_help = QLabel("💡 Define when this item occurs. Examples:\n" +
                            "• Monthly on the 1st: Your rent or mortgage\n" +
                            "• Biweekly on Friday: Paycheck\n" +
                            "• Weekly on Monday: Grocery shopping\n" +
                            "You can add multiple periods for complex schedules.")
        period_help.setStyleSheet("font-size: 10px; padding: 8px; border-radius: 4px;")
        period_help.setWordWrap(True)
        period_outer_layout.addWidget(period_help)
        
        period_layout = QVBoxLayout()
        period_layout.setSpacing(10)

        # Add existing periods if editing
        if budget_item and budget_item.periods:
            for period in budget_item.periods:
                self.add_budget_period(period_layout, True, period)
        else:
            self.add_budget_period(period_layout)
        
        period_outer_layout.addLayout(period_layout)
        
        add_period_button = QPushButton("➕ Add Another Period")
        add_period_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        add_period_button.clicked.connect(
            lambda: self.add_budget_period(period_layout, True)
        )
        period_outer_layout.addWidget(add_period_button)
        
        period_container.setLayout(period_outer_layout)
        vl.addWidget(period_container)

        # Action buttons
        button_hl = QHBoxLayout()
        button_hl.setSpacing(10)
        button_hl.addStretch(1)
        
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        button_hl.addWidget(cancel_button)
        
        save_button = QPushButton(f"✅ {'Update' if budget_item else 'Create'} Budget Item")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        button_hl.addWidget(save_button)
        button_hl.addStretch(1)

        vl.addLayout(button_hl)

        cancel_button.clicked.connect(lambda: self.cancel_edit())
        save_button.clicked.connect(
            lambda: self.save_budget_item(
                name.text(),
                type.currentText(),
                amount.text(),
                group_combo.currentText(),
                start_date.date().toString("yyyy-MM-dd"),
                # Use far future date if "no end date" is checked
                "2999-12-31" if no_end_date_checkbox.isChecked() else end_date.date().toString("yyyy-MM-dd"),
                self.periods_from_layout(period_layout),
            )
        )

        content_widget.setLayout(vl)
        scroll.setWidget(content_widget)
        self.addWidget(scroll)

    def add_budget_group(self, combobox, name):
        self.db.create_budget_group(self.selected_profile.id, name)
        combobox.addItem(name)

    def cancel_edit(self):
        """Cancel editing and return to list."""
        self.editing_budget_item = None
        self.setCurrentIndex(0)
    
    def delete_budget_item(self, budget_item: BudgetItem):
        """Delete a budget item with confirmation."""
        reply = QMessageBox.question(
            self,
            "Delete Budget Item",
            f"Are you sure you want to delete '{budget_item.name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_budget_item(budget_item.id)
            QMessageBox.information(
                self,
                "Success",
                f"Budget item '{budget_item.name}' has been deleted."
            )
            self.render_budget()

    def add_budget_period(self, layout, removable=False, period: BudgetItemPeriod = None):
        hl = QHBoxLayout()

        budget_type = QComboBox()
        budget_type.addItems(
            ["Monthly", "Weekly", "Biweekly", "Daily", "Business Days"]
        )  # , "Yearly"])
        if period:
            budget_type.setCurrentText(period.type)
        hl.addWidget(budget_type)

        budget_value = QComboBox()
        hl.addWidget(budget_value)

        self.update_budget_value(budget_value, budget_type.currentText())
        if period:
            budget_value.setCurrentText(period.value)
        budget_type.currentTextChanged.connect(
            lambda: self.update_budget_value(budget_value, budget_type.currentText())
        )

        business_day = QComboBox()
        business_day.addItems(["None", "Previous", "Next"])
        if period:
            business_day.setCurrentText(period.business_day)
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

    def save_budget_item(
        self, name, type, amount, group, start_date, end_date, periods
    ):
        """Save budget item (create or update)."""
        if self.editing_budget_item:
            # Update existing item
            self.db.update_budget_item(
                self.editing_budget_item.id,
                name,
                type,
                amount,
                group,
                start_date,
                end_date,
                periods,
            )
            self.editing_budget_item = None
        else:
            # Create new item
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
