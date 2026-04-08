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
from ui.onboarding import HelpIcon, HELP_TEXTS


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

    def _clear_all_widgets(self):
        """Remove all widgets from the stacked widget."""
        while self.count() > 0:
            w = self.widget(0)
            self.removeWidget(w)
            w.deleteLater()

    def refresh(self):
        """Re-fetch data from DB and rebuild both the list and form views."""
        self._clear_all_widgets()
        self.render_budget()
        self.render_budget_item_form()

    def render_budget(self):
        widget = QWidget()
        vl = QVBoxLayout()
        vl.setSpacing(20)
        vl.setContentsMargins(20, 20, 20, 20)

        # Title section
        title_container = QWidget()
        title_container.setStyleSheet("padding: 15px;")
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 10, 5)

        budget_title = QLabel("Budget Items")
        budget_title_font = QFont()
        budget_title_font.setPointSize(18)
        budget_title_font.setBold(True)
        budget_title.setFont(budget_title_font)
        title_layout.addWidget(budget_title)
        title_layout.addWidget(HelpIcon(HELP_TEXTS["budget"]))
        title_layout.addStretch(1)

        # Add Budget Item button in title
        createButton = QPushButton("Add Budget Item")
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

        # Budget items table
        self.budget_groups = self.db.fetch_budget_groups(self.selected_profile.id)
        self.budget_items = self.db.fetch_budget_items(self.selected_profile.id)

        if self.budget_items:
            # Table label
            table_label = QLabel(f"{len(self.budget_items)} Budget Items")
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
                name_item = QTableWidgetItem(budget_items.name)
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
                gid = budget_items.budget_group_id
                if isinstance(gid, str):
                    group_name = gid  # Legacy: name stored directly
                else:
                    group = next((g for g in self.budget_groups if g.id == gid), None)
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
                    lambda checked=False, item=budget_items: self.edit_budget_item(item)
                )
                button_layout.addWidget(edit_button)

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
            no_items_container = QWidget()
            no_items_vl = QVBoxLayout()
            no_items_vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_items_title = QLabel("No budget items yet")
            no_items_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ni_font = QFont()
            ni_font.setPointSize(16)
            ni_font.setBold(True)
            no_items_title.setFont(ni_font)
            no_items_vl.addWidget(no_items_title)
            no_items_desc = QLabel(
                "Budget items are your recurring income and expenses — rent, salary, subscriptions, etc.\n"
                "Each item has a schedule that tells Budgie when it occurs.\n\n"
                "Click 'Add Budget Item' above to get started.\n"
                "Once you have items, go to the Calendar tab and run Extrapolation to see them on your schedule."
            )
            no_items_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_items_desc.setWordWrap(True)
            no_items_desc.setStyleSheet("font-size: 13px; padding: 20px;")
            no_items_vl.addWidget(no_items_desc)
            no_items_container.setLayout(no_items_vl)
            vl.addWidget(no_items_container)

        # Budget Overview Chart - expense items grouped by budget group
        self._render_budget_chart(vl)

        # vl.addStretch(1)

        widget.setLayout(vl)
        widget.show()

        self.addWidget(widget)

    def _render_budget_chart(self, parent_layout: QVBoxLayout):
        """Render a horizontal bar chart of expense budget items grouped by budget group."""
        # Collect expense items only
        expense_items = [item for item in self.budget_items if item.type == "Expense"]
        if not expense_items:
            return

        # Group expense amounts by budget_group_id
        group_totals: dict = {}
        group_names: dict = {}
        ungrouped_key = -1

        for item in expense_items:
            gid = item.budget_group_id if item.budget_group_id else ungrouped_key
            group_totals[gid] = group_totals.get(gid, 0.0) + float(item.amount)
            if gid not in group_names:
                if gid == ungrouped_key:
                    group_names[gid] = "Ungrouped"
                elif isinstance(gid, str):
                    # Legacy data: budget_group_id stored as group name string
                    group_names[gid] = gid
                else:
                    group = next((g for g in self.budget_groups if g.id == gid), None)
                    group_names[gid] = group.name if group else "Unknown"

        if not group_totals:
            return

        max_total = max(group_totals.values())
        max_bar_width = 300

        # Color palette for groups
        bar_colors = [
            "#1976d2",  # blue
            "#27ae60",  # green
            "#e67e22",  # orange
            "#8e44ad",  # purple
            "#e74c3c",  # red
            "#16a085",  # teal
            "#f39c12",  # amber
            "#2980b9",  # lighter blue
            "#d35400",  # dark orange
            "#c0392b",  # dark red
        ]

        # Chart container
        chart_container = QWidget()
        chart_container.setStyleSheet("padding: 15px;")
        chart_layout = QVBoxLayout()
        chart_layout.setSpacing(12)
        chart_layout.setContentsMargins(10, 10, 10, 10)

        # Section header
        chart_title = QLabel("Budget Overview")
        chart_title_font = QFont()
        chart_title_font.setPointSize(14)
        chart_title_font.setBold(True)
        chart_title.setFont(chart_title_font)
        chart_layout.addWidget(chart_title)

        # Sort groups by total descending
        sorted_groups = sorted(group_totals.items(), key=lambda x: x[1], reverse=True)

        for idx, (gid, total) in enumerate(sorted_groups):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)

            # Group name label (fixed width for alignment)
            name_label = QLabel(group_names[gid])
            name_label.setFixedWidth(120)
            name_label.setStyleSheet("font-size: 12px; font-weight: bold;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(name_label)

            # Colored bar
            bar_width = int((total / max_total) * max_bar_width) if max_total > 0 else 0
            bar_width = max(bar_width, 4)  # minimum visible width
            color = bar_colors[idx % len(bar_colors)]

            bar = QWidget()
            bar.setFixedWidth(bar_width)
            bar.setFixedHeight(22)
            bar.setStyleSheet(
                f"background-color: {color}; border-radius: 4px; border: none;"
            )
            row_layout.addWidget(bar)

            # Amount label
            amount_label = QLabel(f"${total:,.2f}")
            amount_label.setStyleSheet("font-size: 12px;")
            amount_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(amount_label)

            row_layout.addStretch(1)
            chart_layout.addLayout(row_layout)

        chart_container.setLayout(chart_layout)
        parent_layout.addWidget(chart_container)

    def edit_budget_item(self, budget_item: BudgetItem):
        """Load budget item into form for editing."""
        self.editing_budget_item = budget_item
        self._clear_all_widgets()
        self.render_budget()
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
        content_widget.setMaximumWidth(600)
        vl = QVBoxLayout()
        vl.setSpacing(8)
        vl.setContentsMargins(24, 16, 24, 16)

        # Back button
        back_button = QPushButton("Back to Budget")
        back_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #546e7a;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        back_button.setMaximumWidth(160)
        back_button.clicked.connect(lambda: self.cancel_edit())
        vl.addWidget(back_button)

        vl.addSpacing(8)

        # Title
        title = QLabel(f"{'Edit' if budget_item else 'Create'} Budget Item")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        vl.addWidget(title)

        desc = QLabel("Set up a recurring income or expense that appears in your calendar.")
        desc.setStyleSheet("font-size: 13px;")
        desc.setWordWrap(True)
        vl.addWidget(desc)

        vl.addSpacing(16)

        # ── Helper for section titles ──
        def section_label(text):
            lbl = QLabel(text)
            fnt = QFont()
            fnt.setPointSize(13)
            fnt.setBold(True)
            lbl.setFont(fnt)
            return lbl

        def field_label(text):
            lbl = QLabel(text)
            fnt = QFont()
            fnt.setPointSize(11)
            fnt.setBold(True)
            lbl.setFont(fnt)
            return lbl

        def help_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 12px; font-style: italic; color: #90a4ae;")
            lbl.setWordWrap(True)
            return lbl

        input_style = "padding: 10px; font-size: 14px;"
        input_height = 40

        # ── Basic Information ──
        vl.addWidget(section_label("Basic Information"))
        vl.addSpacing(4)

        vl.addWidget(field_label("Item Name"))
        name = QLineEdit()
        name.setPlaceholderText("e.g., Rent, Salary, Groceries")
        name.setText(budget_item.name if budget_item else "")
        name.setStyleSheet(input_style)
        name.setMinimumHeight(input_height)
        vl.addWidget(name)

        vl.addSpacing(8)

        vl.addWidget(field_label("Type"))
        vl.addWidget(help_label("Is this money coming in (Income) or going out (Expense)?"))
        type = QComboBox()
        type.addItems(["Income", "Expense"])
        if budget_item:
            type.setCurrentText(budget_item.type)
        type.setStyleSheet(input_style)
        type.setMinimumHeight(input_height)
        vl.addWidget(type)

        vl.addSpacing(8)

        vl.addWidget(field_label("Amount"))
        amount = QLineEdit()
        amount.setPlaceholderText("0.00")
        amount.setText(str(budget_item.amount) if budget_item else "")
        amount.setStyleSheet(input_style)
        amount.setMinimumHeight(input_height)
        vl.addWidget(amount)

        vl.addSpacing(20)

        # ── Categorization ──
        vl.addWidget(section_label("Categorization (Optional)"))
        vl.addWidget(help_label("Group similar items together (e.g., 'Housing', 'Transportation')"))
        vl.addSpacing(4)

        existing_groups = self.db.fetch_budget_groups(self.selected_profile.id)
        group_combo = QComboBox()
        group_combo.addItems([group.name for group in existing_groups])
        if budget_item and budget_item.budget_group_id:
            group = next((g for g in existing_groups if g.id == budget_item.budget_group_id), None)
            if group:
                group_combo.setCurrentText(group.name)
        group_combo.setStyleSheet(input_style)
        group_combo.setMinimumHeight(input_height)
        vl.addWidget(group_combo)

        new_group_row = QHBoxLayout()
        new_group_row.setSpacing(8)
        new_group = QLineEdit()
        new_group.setPlaceholderText("Create new group...")
        new_group.setStyleSheet(input_style)
        new_group.setMinimumHeight(input_height)
        new_group_row.addWidget(new_group)
        new_group_create = QPushButton("Add Group")
        new_group_create.setStyleSheet("padding: 10px 16px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px;")
        new_group_create.setMinimumHeight(input_height)
        new_group_create.clicked.connect(
            lambda: self.add_budget_group(group_combo, new_group.text(), new_group)
        )
        new_group_row.addWidget(new_group_create)
        vl.addLayout(new_group_row)

        vl.addSpacing(20)

        # ── Linked Debt ──
        existing_debts = self.db.fetch_debts(self.selected_profile.id)
        vl.addWidget(section_label("Linked Debt (Optional)"))
        vl.addWidget(help_label("Link to a debt for automatic payment capping based on remaining balance."))
        vl.addSpacing(4)

        debt_combo = QComboBox()
        debt_combo.addItem("None", None)
        for debt in existing_debts:
            debt_combo.addItem(f"{debt.name} (${float(debt.remaining_amount):,.2f} remaining)", debt.id)
        if budget_item and budget_item.debt_id:
            for i in range(debt_combo.count()):
                if debt_combo.itemData(i) == budget_item.debt_id:
                    debt_combo.setCurrentIndex(i)
                    break
        debt_combo.setStyleSheet(input_style)
        debt_combo.setMinimumHeight(input_height)
        vl.addWidget(debt_combo)

        vl.addSpacing(20)

        # ── Active Period ──
        vl.addWidget(section_label("Active Period"))
        vl.addWidget(help_label("When should this item be active? For ongoing items, check 'No end date'."))
        vl.addSpacing(4)

        vl.addWidget(field_label("Start Date"))
        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setStyleSheet(input_style)
        start_date.setMinimumHeight(input_height)
        if budget_item:
            start_date.setDate(QDate.fromString(budget_item.start_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        else:
            start_date.setDate(QDate.currentDate())
        vl.addWidget(start_date)

        vl.addSpacing(8)

        no_end_date_checkbox = QCheckBox("No end date (ongoing)")
        no_end_date_checkbox.setStyleSheet("font-size: 13px;")
        if budget_item:
            has_end_date = budget_item.end_date.year < 2100
            no_end_date_checkbox.setChecked(not has_end_date)
        else:
            no_end_date_checkbox.setChecked(True)
        vl.addWidget(no_end_date_checkbox)

        vl.addWidget(field_label("End Date"))
        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        end_date.setStyleSheet(input_style)
        end_date.setMinimumHeight(input_height)
        if budget_item and budget_item.end_date.year < 2100:
            end_date.setDate(QDate.fromString(budget_item.end_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        else:
            end_date.setDate(QDate.currentDate().addYears(1))

        def toggle_end_date(checked):
            end_date.setEnabled(not checked)

        no_end_date_checkbox.toggled.connect(toggle_end_date)
        end_date.setEnabled(not no_end_date_checkbox.isChecked())
        vl.addWidget(end_date)

        vl.addSpacing(20)

        # ── Recurrence Schedule ──
        vl.addWidget(section_label("Recurrence Schedule"))
        vl.addWidget(help_label(
            "Define when this item occurs. Examples:\n"
            "  Monthly on the 1st — Rent or mortgage\n"
            "  Biweekly on Friday — Paycheck\n"
            "  Weekly on Monday — Grocery shopping"
        ))
        
        vl.addSpacing(4)

        period_layout = QVBoxLayout()
        period_layout.setSpacing(10)

        if budget_item and budget_item.periods:
            for period in budget_item.periods:
                self.add_budget_period(period_layout, True, period)
        else:
            self.add_budget_period(period_layout)

        vl.addLayout(period_layout)

        add_period_button = QPushButton("Add Another Period")
        add_period_button.setStyleSheet("padding: 10px 16px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px;")
        add_period_button.setMinimumHeight(40)
        add_period_button.clicked.connect(
            lambda: self.add_budget_period(period_layout, True)
        )
        vl.addWidget(add_period_button)

        vl.addSpacing(24)

        # Action buttons
        button_hl = QHBoxLayout()
        button_hl.setSpacing(12)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("padding: 12px 24px; border: 1px solid #546e7a; border-radius: 6px; font-size: 14px; font-weight: bold;")
        cancel_button.setMinimumHeight(44)
        button_hl.addWidget(cancel_button)

        save_button = QPushButton(f"{'Update' if budget_item else 'Create'} Budget Item")
        save_button.setStyleSheet("padding: 12px 24px; border: 1px solid #546e7a; border-radius: 6px; font-size: 14px; font-weight: bold;")
        save_button.setMinimumHeight(44)
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
                debt_combo.currentData(),
            )
        )

        content_widget.setLayout(vl)
        scroll.setWidget(content_widget)
        self.addWidget(scroll)

    def add_budget_group(self, combobox, name, input_widget=None):
        if not name.strip():
            QMessageBox.warning(self, "Invalid Input", "Please enter a group name.")
            return
        try:
            self.db.create_budget_group(self.selected_profile.id, name)
            combobox.addItem(name)
            combobox.setCurrentText(name)
            if input_widget:
                input_widget.clear()
            QMessageBox.information(self, "Success", f"Budget group '{name}' created.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create group: {str(e)}")

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
            try:
                self.db.delete_budget_item(budget_item.id)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Budget item '{budget_item.name}' has been deleted."
                )
                self.refresh()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to delete budget item: {str(e)}"
                )

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
        # Remove all child widgets from the layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
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
        self, name, type, amount, group, start_date, end_date, periods, debt_id=None
    ):
        """Save budget item (create or update)."""
        try:
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
                    debt_id=debt_id,
                )
                self.editing_budget_item = None
                QMessageBox.information(
                    self, "Success", f"Budget item '{name}' updated successfully!"
                )
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
                    debt_id=debt_id,
                )
                QMessageBox.information(
                    self, "Success", f"Budget item '{name}' created successfully!"
                )
            self.refresh()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save budget item: {str(e)}"
            )
