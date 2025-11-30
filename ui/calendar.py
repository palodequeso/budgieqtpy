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
    QMessageBox,
    QScrollArea,
)
from PyQt6.QtGui import QColor, QBrush, QFont, QPalette
from PyQt6.QtCore import pyqtSlot as Slot, QTimer, QEvent
from PyQt6.QtWidgets import QApplication
from database.database import Database
from database.extrapolation_item import ExtrapolationItem
from database.profile import Profile
from shedule.schedule import Schedule
from shedule.schedule_entry import ScheduleEntry
from shedule.schedule_entry_item import ScheduleEntryItem

# Import services (shared business logic)
from services import CalendarService, LedgerService

locale.setlocale(locale.LC_ALL, "C")

# Dark mode colors (darker shades with white text)
MONTH_COLORS_DARK = [
    QColor("#8B1515"),  # Red - darker than 900
    QColor("#6B0A3C"),  # Pink - darker than 900
    QColor("#380F6B"),  # Purple - darker than 900
    QColor("#9D6A0A"),  # Yellow/Gold - much darker for contrast
    QColor("#B84000"),  # Orange - darker than 900
    QColor("#0A3677"),  # Blue - darker than 900
    QColor("#014477"),  # Light Blue - darker than 900
    QColor("#004D50"),  # Cyan - darker than 900
    QColor("#003D32"),  # Teal - darker than 900
    QColor("#154718"),  # Green - darker than 900
    QColor("#285216"),  # Light Green - darker than 900
    QColor("#665E12"),  # Lime/Olive - darker than 900
    QColor("#1C262B"),  # Blue Grey - darker than 900
    # alt colors (900 shades for variety)
    QColor("#B71C1C"),  # Red 900
    QColor("#880E4F"),  # Pink 900
    QColor("#4A148C"),  # Purple 900
    QColor("#C67D0D"),  # Yellow/Gold - darker custom shade
    QColor("#E65100"),  # Orange 900
    QColor("#0D47A1"),  # Blue 900
    QColor("#01579B"),  # Light Blue 900
    QColor("#006064"),  # Cyan 900
    QColor("#004D40"),  # Teal 900
    QColor("#1B5E20"),  # Green 900
    QColor("#33691E"),  # Light Green 900
    QColor("#827717"),  # Lime 900
    QColor("#263238"),  # Blue Grey 900
]

# Light mode colors (lighter shades with dark text)
MONTH_COLORS_LIGHT = [
    QColor("#FFCDD2"),  # Red 100
    QColor("#F8BBD0"),  # Pink 100
    QColor("#E1BEE7"),  # Purple 100
    QColor("#FFF9C4"),  # Yellow 100
    QColor("#FFE0B2"),  # Orange 100
    QColor("#BBDEFB"),  # Blue 100
    QColor("#B3E5FC"),  # Light Blue 100
    QColor("#B2EBF2"),  # Cyan 100
    QColor("#B2DFDB"),  # Teal 100
    QColor("#C8E6C9"),  # Green 100
    QColor("#DCEDC8"),  # Light Green 100
    QColor("#F0F4C3"),  # Lime 100
    QColor("#CFD8DC"),  # Blue Grey 100
    # alt colors (200 shades for variety)
    QColor("#EF9A9A"),  # Red 200
    QColor("#F48FB1"),  # Pink 200
    QColor("#CE93D8"),  # Purple 200
    QColor("#FFF59D"),  # Yellow 200
    QColor("#FFCC80"),  # Orange 200
    QColor("#90CAF9"),  # Blue 200
    QColor("#81D4FA"),  # Light Blue 200
    QColor("#80DEEA"),  # Cyan 200
    QColor("#80CBC4"),  # Teal 200
    QColor("#A5D6A7"),  # Green 200
    QColor("#C5E1A5"),  # Light Green 200
    QColor("#E6EE9C"),  # Lime 200
    QColor("#B0BEC5"),  # Blue Grey 200
]


class Calendar(QWidget):
    db: Database = None
    selected_profile: Profile = None
    schedule: Schedule = None
    grid_entries: dict[int, ScheduleEntry] = None
    entry_widget: QWidget = None
    schedule_widget: QWidget = None
    schedule_container_layout: QVBoxLayout = None
    
    # Services (shared with API)
    calendar_service: CalendarService = None
    ledger_service: LedgerService = None
    
    # UI references
    extrapolation_start_date: QDateEdit = None
    extrapolation_end_date: QDateEdit = None
    fix_unscheduled_button: QPushButton = None

    def __init__(self, db, selected_profile):
        super().__init__()
        self.db = db
        self.selected_profile = selected_profile
        
        # Initialize services (same logic as API!)
        self.calendar_service = CalendarService(db)
        self.ledger_service = LedgerService(db)
        
        # Load initial schedule using service
        self.schedule = Schedule()
        self.schedule.fetch_schedule(self.db, self.selected_profile.id)
        self.schedule.build_schedule()
        
        self.grid_entries = {}
        self.entry_widget = None
        self.schedule_widget = None

        self.schedule_vertical_layout = QVBoxLayout()
        self.schedule_vertical_layout.setSpacing(12)
        self.schedule_vertical_layout.setContentsMargins(12, 12, 12, 12)

        # Title section
        title_container = QWidget()
        title_container.setStyleSheet("border-radius: 6px; padding: 12px;")
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        calendar_title = QLabel("📅 Budget Calendar")
        calendar_title_font = QFont()
        calendar_title_font.setPointSize(18)
        calendar_title_font.setBold(True)
        calendar_title.setFont(calendar_title_font)
        title_layout.addWidget(calendar_title)
        title_layout.addStretch(1)
        
        title_container.setLayout(title_layout)
        self.schedule_vertical_layout.addWidget(title_container)

        # Controls container
        controls_container = QWidget()
        controls_container.setStyleSheet("border-radius: 6px; padding: 12px;")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(12)
        
        # Date range row
        date_row = QHBoxLayout()
        date_row.setSpacing(10)
        
        date_range_label = QLabel("Extrapolation Period:")
        date_range_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        date_row.addWidget(date_range_label)
        
        self.extrapolation_start_date = QDateEdit()
        self.extrapolation_start_date.setDate(date.today())
        self.extrapolation_start_date.setCalendarPopup(True)
        date_row.addWidget(self.extrapolation_start_date)
        
        date_to_label = QLabel("to")
        date_to_label.setStyleSheet("font-size: 12px; margin: 0 5px;")
        date_row.addWidget(date_to_label)
        
        self.extrapolation_end_date = QDateEdit()
        self.extrapolation_end_date.setDate(date.today() + timedelta(days=365))
        self.extrapolation_end_date.setCalendarPopup(True)
        date_row.addWidget(self.extrapolation_end_date)
        
        date_row.addStretch(1)
        controls_layout.addLayout(date_row)
        
        # Action buttons row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        
        # Primary action - Extrapolate
        extrapolate_button = QPushButton("🔄 Extrapolate")
        extrapolate_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        extrapolate_button.clicked.connect(
            lambda: self.extrapolate_budget(self.schedule_vertical_layout)
        )
        actions_row.addWidget(extrapolate_button)
        
        # Success action - I Got Paid
        got_paid_button = QPushButton("💰 I Got Paid")
        got_paid_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        got_paid_button.clicked.connect(self.got_paid)
        actions_row.addWidget(got_paid_button)
        
        # Warning action - Fix Unscheduled
        self.fix_unscheduled_button = QPushButton("⚠️ Fix Unscheduled")
        self.fix_unscheduled_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #c0392b;
            }
            QPushButton:pressed:enabled {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        self.fix_unscheduled_button.clicked.connect(self.fix_unscheduled)
        self.fix_unscheduled_button.setEnabled(False)
        actions_row.addWidget(self.fix_unscheduled_button)
        
        actions_row.addStretch(1)
        
        # Secondary actions
        add_one_off_button = QPushButton("➕ Add One-Off")
        add_one_off_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        add_one_off_button.clicked.connect(self.add_one_off_entry)
        actions_row.addWidget(add_one_off_button)
        
        add_savings_items_button = QPushButton("💎 Add Savings")
        add_savings_items_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        add_savings_items_button.clicked.connect(self.set_savings_items)
        actions_row.addWidget(add_savings_items_button)
        
        hide_current_column_button = QPushButton("👁️ Hide Column")
        hide_current_column_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        hide_current_column_button.clicked.connect(self.hide_current_column)
        actions_row.addWidget(hide_current_column_button)
        
        export_spreadsheet_button = QPushButton("📊 Export")
        export_spreadsheet_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        export_spreadsheet_button.clicked.connect(self.export_spreadsheet)
        actions_row.addWidget(export_spreadsheet_button)
        
        controls_layout.addLayout(actions_row)
        controls_container.setLayout(controls_layout)
        self.schedule_vertical_layout.addWidget(controls_container)

        self.schedule_container_layout = QVBoxLayout()
        self.schedule_vertical_layout.addLayout(self.schedule_container_layout)

        self.setLayout(self.schedule_vertical_layout)

        self.render_schedule(self.schedule_container_layout)
    
    def changeEvent(self, event):
        """Handle theme changes by refreshing calendar colors."""
        if event.type() == QEvent.Type.PaletteChange:
            # Theme has changed, defer refresh to avoid segfault
            # Use QTimer to ensure event processing completes before widget modification
            if hasattr(self, 'schedule_container_layout') and self.schedule_container_layout:
                QTimer.singleShot(100, lambda: self.render_schedule(self.schedule_container_layout))
        super().changeEvent(event)

    def is_dark_mode(self):
        """Detect if the application is in dark mode."""
        # Use widget's own palette to detect theme
        palette = self.palette()
        
        # Check Base color (used for input fields) - more reliable for theme detection
        base_color = palette.color(QPalette.ColorRole.Base)
        base_luminance = (base_color.red() + base_color.green() + base_color.blue()) / 3
        
        # Also check Window background
        window_color = palette.color(QPalette.ColorRole.Window)
        window_luminance = (window_color.red() + window_color.green() + window_color.blue()) / 3
        
        # Use average background luminance to determine theme
        # If background is dark (< 128), it's dark mode
        # If background is light (>= 128), it's light mode
        avg_bg_luminance = (base_luminance + window_luminance) / 2
        return avg_bg_luminance < 128
    
    def date_to_color(self, date, dull=False):
        colors = MONTH_COLORS_DARK if self.is_dark_mode() else MONTH_COLORS_LIGHT
        if dull:
            if date.day >= 15:
                return colors[25]
            return colors[12]
        if date.day >= 15:
            return colors[(date.month - 1) + 13]
        return colors[date.month - 1]

    def format_currency(self, amount):
        return "${:,.2f}".format(amount)
        # return locale.currency(amount, grouping=True)

    def create_cell(self, date, value: float, bold=False, dull=False, paid=False):
        out_str = ""
        if value is not None:
            out_str = self.format_currency(value)
        item = QTableWidgetItem(out_str)
        item.setBackground(QBrush(self.date_to_color(date, dull)))
        # Set text color based on theme
        text_color = QColor("#FFFFFF") if self.is_dark_mode() else QColor("#000000")
        item.setForeground(QBrush(text_color))
        if bold:
            f = QFont()
            f.setBold(True)
            item.setFont(f)
        if paid:
            f = QFont()
            f.setStrikeOut(True)
            item.setFont(f)
        return item

    def export_spreadsheet(self):
        """Export schedule to ODS spreadsheet file."""
        from PyQt6.QtWidgets import QFileDialog
        
        if not self.selected_profile:
            QMessageBox.warning(self, "No Profile", "Please select a profile first.")
            return
        
        # Open file save dialog
        default_filename = f"budget-schedule-{date.today().strftime('%Y-%m-%d')}.ods"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Spreadsheet",
            default_filename,
            "ODS Files (*.ods);;All Files (*)"
        )
        
        if not file_path:
            # User cancelled
            return
        
        try:
            # Use calendar service to generate spreadsheet
            result = self.calendar_service.download_spreadsheet(self.selected_profile.id)
            
            # Copy the generated file to the user's chosen location
            import shutil
            shutil.copy(result["path"], file_path)
            
            QMessageBox.information(
                self,
                "Success",
                f"Spreadsheet exported successfully to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export spreadsheet:\n{str(e)}"
            )

    def hide_current_column(self):
        """Hide the leftmost visible (oldest non-hidden) income date column."""
        if not self.schedule.sorted_income_dates:
            QMessageBox.warning(self, "No Columns", "No income dates to hide.")
            return
        
        # Filter to get visible dates only (same logic as render_schedule)
        visible_income_dates = []
        for income_date in self.schedule.sorted_income_dates:
            # Skip dates that are hidden (before or equal to hidden_through)
            if self.selected_profile.hidden_through:
                hidden_date = date.fromisoformat(self.selected_profile.hidden_through) if isinstance(self.selected_profile.hidden_through, str) else self.selected_profile.hidden_through
                if income_date <= hidden_date:
                    continue  # Skip this column
            visible_income_dates.append(income_date)
        
        if not visible_income_dates:
            QMessageBox.warning(self, "No Visible Columns", "No visible income dates to hide.")
            return
        
        current_column_income_date = visible_income_dates[0]
        date_key = current_column_income_date.strftime("%Y-%m-%d")
        column = self.schedule.columns.get(date_key)
        
        if not column:
            QMessageBox.warning(self, "Error", "Column not found.")
            return
        
        # Check if all items in this column are paid
        all_paid = True
        unpaid_items = []
        for expense in column.expenses:
            for item in expense.items:
                if item.ledger_entry is None:
                    all_paid = False
                    unpaid_items.append(item.extrapolation_item)
        
        # Create confirmation dialog
        hide_dialog = QDialog(self)
        hide_dialog.setWindowTitle("Hide Column")
        hide_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(f"Income Date: {current_column_income_date.strftime('%Y-%m-%d')}"))
        layout.addWidget(QLabel(f"Ending Balance: {self.format_currency(column.total())}"))
        
        if not all_paid:
            layout.addWidget(QLabel(f"\n⚠️ Warning: {len(unpaid_items)} unpaid item(s) in this column!"))
            layout.addWidget(QLabel("Items will remain in database but hidden from view."))
        else:
            layout.addWidget(QLabel("\n✅ All items in this column are paid."))
        
        layout.addWidget(QLabel("\nHiding this column will remove it from the schedule view."))
        
        layout.addStretch(1)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(hide_dialog.reject)
        buttons_layout.addWidget(cancel_button)
        
        hide_button = QPushButton("Hide Column")
        hide_button.clicked.connect(lambda: self._do_hide_column(current_column_income_date, hide_dialog))
        buttons_layout.addWidget(hide_button)
        
        layout.addLayout(buttons_layout)
        hide_dialog.setLayout(layout)
        hide_dialog.exec()
    
    def _do_hide_column(self, income_date: date, dialog: QDialog):
        """Hide the column by updating profile.hidden_through date."""
        try:
            date_key = income_date.strftime("%Y-%m-%d")
            
            # Update profile's hidden_through field
            # This will hide all columns up to and including this date
            self.db.update_profile_hidden_through(self.selected_profile.id, date_key)
            
            # Update the selected_profile object
            self.selected_profile.hidden_through = date_key
            
            dialog.accept()
            
            # Refresh schedule (will now filter based on hidden_through)
            self._refresh_schedule()
            
            QMessageBox.information(
                self, "Success",
                f"Columns through {date_key} are now hidden.\n\nTo unhide, adjust the profile's hidden_through date in settings."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to hide column: {str(e)}")

    def select_entry(self, entry: ScheduleEntry):
        """Open modal dialog to view and edit schedule entry (matches React pattern)."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Schedule Entry - {entry.budget_item.name}")
        dialog.resize(700, 600)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Entry summary section
        summary_widget = QWidget()
        summary_widget.setStyleSheet("padding: 12px; border-radius: 6px;")
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(6)
        
        title_label = QLabel(entry.budget_item.name)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        summary_layout.addWidget(title_label)
        
        type_label = QLabel(f"Type: {entry.budget_item.type}")
        type_label.setStyleSheet("font-size: 12px;")
        summary_layout.addWidget(type_label)
        
        amount_label = QLabel(f"Budget Item Amount: ${entry.budget_item.amount:,.2f}")
        amount_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        summary_layout.addWidget(amount_label)
        
        date_label = QLabel(f"Income Date: {entry.income_date.strftime('%Y-%m-%d')}")
        date_label.setStyleSheet("font-size: 11px;")
        summary_layout.addWidget(date_label)
        
        total_label = QLabel(f"Entry Total: {self.format_currency(entry.total())}")
        total_label.setStyleSheet("color: #3498db; font-size: 13px; font-weight: bold;")
        summary_layout.addWidget(total_label)
        
        summary_widget.setLayout(summary_layout)
        layout.addWidget(summary_widget)
        
        # Items section with header
        items_header = QLabel(f"📋 Scheduled Expenses ({len(entry.items)} item{'s' if len(entry.items) != 1 else ''})")
        items_header_font = QFont()
        items_header_font.setPointSize(13)
        items_header_font.setBold(True)
        items_header.setFont(items_header_font)
        items_header.setStyleSheet("margin-top: 4px;")
        layout.addWidget(items_header)
        
        # Scrollable items list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        for idx, item in enumerate(entry.items):
            item_container = QWidget()
            item_container.setStyleSheet("padding: 10px; margin: 3px 0; border-radius: 4px;")
            item_layout = QHBoxLayout()
            item_layout.setSpacing(10)
            
            # Item number for multiple items
            if len(entry.items) > 1:
                num_label = QLabel(f"#{idx + 1}")
                num_label.setStyleSheet("font-weight: bold; font-size: 11px;")
                item_layout.addWidget(num_label)
            
            # Date
            date_label = QLabel(f"📅 {item.extrapolation_item.due_date.strftime('%Y-%m-%d')}")
            date_label.setMinimumWidth(110)
            date_label.setStyleSheet("font-size: 11px;")
            item_layout.addWidget(date_label)
            
            # Amount
            amount = item.ledger_entry.amount if item.ledger_entry is not None else item.extrapolation_item.amount
            amount_label = QLabel(f"${amount:,.2f}")
            amount_label.setMinimumWidth(100)
            amount_label.setStyleSheet("font-size: 12px; font-weight: bold;")
            item_layout.addWidget(amount_label)
            
            item_layout.addStretch(1)
            
            # Status / Action
            if item.ledger_entry is not None:
                paid_label = QLabel("✅ Paid")
                paid_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
                item_layout.addWidget(paid_label)
            else:
                mark_paid_button = QPushButton("💳 Mark as Paid")
                mark_paid_button.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        padding: 6px 14px;
                        border: none;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #5dade2;
                    }
                """)
                mark_paid_button.clicked.connect(
                    lambda checked=False, i=item, e=entry, d=dialog: self.mark_paid_and_refresh(i, e, d)
                )
                item_layout.addWidget(mark_paid_button)
            
            item_container.setLayout(item_layout)
            scroll_layout.addWidget(item_container)
        
        scroll_layout.addStretch(1)
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        close_button = QPushButton("✕ Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 8px 24px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def mark_paid_and_refresh(self, item: ScheduleEntryItem, entry: ScheduleEntry, parent_dialog: QDialog):
        """Open mark paid dialog, then refresh schedule and close parent dialog after successful payment."""
        # Store parent dialog reference
        self._parent_dialog = parent_dialog
        # Call the existing mark_paid method which will open its own dialog
        self.mark_paid(item, entry)

    def got_paid(self):
        accounts = self.db.fetch_accounts(self.selected_profile.id)

        got_paid_dialog = QDialog()
        got_paid_dialog.setWindowTitle("Got Paid")
        got_paid_dialog.setMinimumWidth(400)
        got_paid_layout = QVBoxLayout()
        got_paid_layout.setSpacing(12)
        got_paid_layout.setContentsMargins(16, 16, 16, 16)

        dialog_label = QLabel("🎉 Hooray, it's payday!")
        dialog_label_font = QFont()
        dialog_label_font.setPointSize(14)
        dialog_label_font.setBold(True)
        dialog_label.setFont(dialog_label_font)
        dialog_label.setStyleSheet("margin-bottom: 8px;")
        got_paid_layout.addWidget(dialog_label)

        # Filter to only show dates where income hasn't been marked as paid
        unpaid_income_dates = []
        for income_date in self.schedule.sorted_income_dates:
            date_key = income_date.strftime("%Y-%m-%d")
            column = self.schedule.columns.get(date_key)
            if column and column.incomes:
                # Check if the income entry is unpaid
                income_entry = column.incomes[0]
                if not income_entry.all_paid():
                    unpaid_income_dates.append(income_date)
        
        if not unpaid_income_dates:
            QMessageBox.information(
                self,
                "All Paid",
                "All income dates have already been marked as paid!"
            )
            return

        # Income date selection
        date_label = QLabel("Income Date")
        date_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 4px;")
        got_paid_layout.addWidget(date_label)
        
        income_date_selector = QComboBox()
        income_date_selector.addItems(
            [x.strftime("%Y-%m-%d") for x in unpaid_income_dates]
        )
        got_paid_layout.addWidget(income_date_selector)

        # Account selection
        account_label = QLabel("Deposit to Account")
        account_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        got_paid_layout.addWidget(account_label)
        
        account_selector = QComboBox()
        for account in accounts:
            account_selector.addItem(account.name)
        got_paid_layout.addWidget(account_selector)

        got_paid_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        cancel_button.clicked.connect(lambda: got_paid_dialog.close())
        buttons_layout.addWidget(cancel_button)
        
        save_button = QPushButton("💰 Mark as Received")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
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
        mark_paid_dialog.setWindowTitle("Mark as Paid")
        mark_paid_dialog.setMinimumWidth(450)
        mark_paid_layout = QVBoxLayout()
        mark_paid_layout.setSpacing(12)
        mark_paid_layout.setContentsMargins(16, 16, 16, 16)

        # Header section
        header_widget = QWidget()
        header_widget.setStyleSheet("padding: 12px; border-radius: 6px;")
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        name_label = QLabel("💳 " + entry.budget_item.name)
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        name_label.setFont(name_font)
        header_layout.addWidget(name_label)
        
        type_label = QLabel(f"Type: {entry.budget_item.type}")
        type_label.setStyleSheet("font-size: 11px;")
        header_layout.addWidget(type_label)
        
        income_date_label = QLabel(f"Income Date: {entry.income_date.strftime('%Y-%m-%d')}")
        income_date_label.setStyleSheet("font-size: 11px;")
        header_layout.addWidget(income_date_label)
        
        due_date_label = QLabel(f"Due Date: {item.extrapolation_item.due_date.strftime('%Y-%m-%d')}")
        due_date_label.setStyleSheet("color: #3498db; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(due_date_label)
        
        header_widget.setLayout(header_layout)
        mark_paid_layout.addWidget(header_widget)

        # Account selection
        account_label = QLabel("Account")
        account_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        mark_paid_layout.addWidget(account_label)
        
        account_help = QLabel("Which account was this paid from?")
        account_help.setStyleSheet("font-size: 10px; font-style: italic;")
        mark_paid_layout.addWidget(account_help)
        
        account_combobox = QComboBox()
        for account in accounts:
            account_combobox.addItem(account.name)
        mark_paid_layout.addWidget(account_combobox)

        # Amount
        amount_label = QLabel("Actual Paid Amount")
        amount_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        mark_paid_layout.addWidget(amount_label)
        
        paid_amount_widget = QLineEdit()
        paid_amount_widget.setText(str(item.extrapolation_item.amount))
        mark_paid_layout.addWidget(paid_amount_widget)

        # Date
        date_label = QLabel("Actual Paid Date")
        date_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        mark_paid_layout.addWidget(date_label)
        
        paid_date_widget = QDateEdit()
        paid_date_widget.setDate(date.today())
        paid_date_widget.setCalendarPopup(True)
        mark_paid_layout.addWidget(paid_date_widget)

        mark_paid_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        buttons_layout.addWidget(cancel_button)
        cancel_button.clicked.connect(lambda: mark_paid_dialog.close())
        
        ok_button = QPushButton("✅ Save Payment")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
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
        """Mark item as paid using service (same logic as API!)."""
        try:
            # Use service to mark item as paid (same logic as API!)
            # Service handles date conversion from string to date object
            ledger = self.ledger_service.mark_extrapolation_item_paid(
                extrapolation_item_id=item.extrapolation_item.id,
                account_id=account_id,
                paid_date=paid_date.isoformat() if hasattr(paid_date, 'isoformat') else paid_date
            )
            
            # Note: Each extrapolation item gets its own ledger entry
            # This respects the UNIQUE constraint on ledger_entry_id
            # If there are multiple items for the same budget item, mark each separately
            
            QMessageBox.information(
                self, "Success",
                f"Item marked as paid. Ledger entry {ledger.id} created."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to mark item as paid: {str(e)}")
            return

        modal.accept()
        
        # If we came from the entry dialog, close it too
        if hasattr(self, '_parent_dialog') and self._parent_dialog:
            self._parent_dialog.accept()
            self._parent_dialog = None
        
        # Use QTimer to defer UI refresh until after event handler completes
        # This prevents segfault by ensuring all dialogs are fully destroyed
        # before we delete/recreate widgets in render_schedule
        QTimer.singleShot(100, lambda: self._refresh_schedule())
    
    def _refresh_schedule(self):
        """Refresh schedule display - called after dialogs are fully closed."""
        self.schedule.fetch_schedule(self.db, self.selected_profile.id)
        self.schedule.build_schedule()
        self.render_schedule(self.schedule_container_layout)

    @Slot(QTableWidgetItem)
    def cell_clicked(self, item):
        entry = self.grid_entries.get((item.row(), item.column()), None)
        if entry is None:
            return

        self.select_entry(entry)

    def add_one_off_entry(self):
        one_off_dialog = QDialog()
        one_off_dialog.setWindowTitle("Add One-Off Entry")
        one_off_dialog.setMinimumWidth(450)
        one_off_layout = QVBoxLayout()
        one_off_layout.setSpacing(12)
        one_off_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_label = QLabel("➕ Add One-Off Entry")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setStyleSheet("margin-bottom: 8px;")
        one_off_layout.addWidget(header_label)
        
        desc_label = QLabel("Create a single non-recurring budget entry")
        desc_label.setStyleSheet("font-size: 11px; margin-bottom: 8px;")
        one_off_layout.addWidget(desc_label)

        # Name
        name_label = QLabel("Name")
        name_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        one_off_layout.addWidget(name_label)
        
        name_widget = QLineEdit()
        name_widget.setPlaceholderText("e.g., Car Repair")
        one_off_layout.addWidget(name_widget)

        # Amount
        amount_label = QLabel("Amount")
        amount_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        one_off_layout.addWidget(amount_label)
        
        amount_widget = QLineEdit('0.00')
        one_off_layout.addWidget(amount_widget)

        # Type
        type_label = QLabel("Type")
        type_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        one_off_layout.addWidget(type_label)
        
        type_widget = QComboBox()
        type_widget.addItem("Expense")
        type_widget.addItem("Income")
        one_off_layout.addWidget(type_widget)

        # Due Date
        date_label = QLabel("Due Date")
        date_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        one_off_layout.addWidget(date_label)
        
        date_widget = QDateEdit(date.today())
        date_widget.setCalendarPopup(True)
        one_off_layout.addWidget(date_widget)

        # Income Date
        income_date_label = QLabel("Income Date")
        income_date_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        one_off_layout.addWidget(income_date_label)
        
        income_date_widget = QComboBox()
        income_date_widget.addItems([x.strftime("%Y-%m-%d") for x in self.schedule.sorted_income_dates])
        one_off_layout.addWidget(income_date_widget)

        # Paid checkbox
        paid_widget = QCheckBox("Mark as already paid")
        paid_widget.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                margin-top: 8px;
            }
        """)
        one_off_layout.addWidget(paid_widget)
        
        # Account (only enabled if paid)
        account_label = QLabel("Account")
        account_label.setStyleSheet("font-size: 11px; font-weight: bold; margin-top: 8px;")
        one_off_layout.addWidget(account_label)
        
        account_widget = QComboBox()
        accounts = self.db.fetch_accounts(self.selected_profile.id)
        for account in accounts:
            account_widget.addItem(account.name)
        account_widget.setEnabled(False)
        paid_widget.checkStateChanged.connect(lambda: account_widget.setEnabled(paid_widget.isChecked()))
        one_off_layout.addWidget(account_widget)

        one_off_layout.addStretch(1)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        cancel_button.clicked.connect(lambda: one_off_dialog.close())
        buttons_layout.addWidget(cancel_button)
        
        ok_button = QPushButton("✅ Save Entry")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        ok_button.clicked.connect(
            lambda: self.save_one_off_entry(
                name_widget.text(),
                float(amount_widget.text() or 0),
                type_widget.currentText(),
                date_widget.date().toPyDate(),
                income_date_widget.currentText(),
                paid_widget.isChecked(),
                accounts[account_widget.currentIndex()] if paid_widget.isChecked() else None,
                one_off_dialog
            )
        )
        buttons_layout.addWidget(ok_button)
        one_off_layout.addLayout(buttons_layout)

        one_off_dialog.setLayout(one_off_layout)
        one_off_dialog.exec()

    def save_one_off_entry(self, name, amount, entry_type, due_date, income_date, is_paid, account, dialog):
        """Save a one-off budget entry."""
        try:
            # Create ledger entry directly (simpler than creating budget item + extrapolation)
            ledger_entry = self.db.create_ledger_entry(
                name=name,
                date=due_date,
                incomeDate=date.fromisoformat(income_date) if isinstance(income_date, str) else income_date,
                type=entry_type,
                amount=-amount if entry_type == "Expense" else amount,
                accountId=account.id if account and is_paid else self.db.fetch_accounts(self.selected_profile.id)[0].id
            )
            
            QMessageBox.information(
                self, "Success",
                f"One-off entry '{name}' created successfully!"
            )
            
            dialog.accept()
            
            # Use QTimer to defer UI refresh - same as mark_paid_with_ledger
            QTimer.singleShot(100, lambda: self._refresh_schedule())
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create one-off entry: {str(e)}")

    def fix_unscheduled(self):
        """Show dialog to manually assign income dates to unscheduled items."""
        if not self.schedule.unscheduled_entries:
            QMessageBox.information(
                self, "No Unscheduled Items",
                "All budget items have been successfully scheduled!"
            )
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Fix Unscheduled Items")
        dialog.setMinimumWidth(650)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_label = QLabel(f"⚠️ Fix Unscheduled Items")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setStyleSheet("color: #ecf0f1; margin-bottom: 4px;")
        layout.addWidget(header_label)
        
        desc_label = QLabel(f"{len(self.schedule.unscheduled_entries)} item(s) could not be automatically scheduled. Manually assign an income date to each item:")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #bdc3c7; font-size: 11px; margin-bottom: 8px;")
        layout.addWidget(desc_label)
        
        # Scrollable area for items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(8)
        
        # Store assignments
        assignments = {}
        
        # Create a row for each unscheduled item
        for entry in self.schedule.unscheduled_entries:
            item_container = QWidget()
            item_container.setStyleSheet("padding: 10px; border-radius: 4px;")
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(0, 0, 0, 0)
            
            # Item info
            info_label = QLabel(f"💸 {entry.name} - {self.format_currency(entry.amount)} (Due: {entry.due_date.strftime('%Y-%m-%d')})")
            info_label.setMinimumWidth(320)
            info_label.setStyleSheet("color: #ecf0f1; font-size: 11px; font-weight: 500;")
            item_layout.addWidget(info_label)
            
            # Income date picker
            income_date_combo = QComboBox()
            income_date_combo.addItem("-- Select Income Date --", None)
            for income_date in self.schedule.sorted_income_dates:
                income_date_combo.addItem(
                    income_date.strftime("%Y-%m-%d"),
                    income_date
                )
            income_date_combo.setStyleSheet("""
                QComboBox {
                    padding: 6px;
                    border: 1px solid #4a5f7f;
                    border-radius: 4px;
                    background-color: #34495e;
                    color: #ecf0f1;
                    font-size: 11px;
                    min-width: 140px;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 5px solid #ecf0f1;
                    margin-right: 5px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                    selection-background-color: #3498db;
                    selection-color: white;
                    border: 1px solid #4a5f7f;
                }
            """)
            item_layout.addWidget(income_date_combo)
            
            # Store reference
            assignments[entry] = income_date_combo
            
            item_container.setLayout(item_layout)
            scroll_layout.addWidget(item_container)
        
        scroll_layout.addStretch(1)
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)
        
        save_button = QPushButton("✅ Save Assignments")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        save_button.clicked.connect(
            lambda: self._save_unscheduled_assignments(assignments, dialog)
        )
        buttons_layout.addWidget(save_button)
        
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        dialog.exec()
    
    def _save_unscheduled_assignments(self, assignments: dict, dialog: QDialog):
        """Save the income date assignments for unscheduled items."""
        try:
            items_to_fix = []
            
            # Collect assignments
            for entry, combo in assignments.items():
                selected_date = combo.currentData()
                if selected_date:
                    # Find the extrapolation item for this entry
                    # The entry should have a budget_item_id we can use
                    extrap_items = self.db.fetch_extrapolation_items(self.selected_profile.id)
                    for item in extrap_items:
                        if (item.budget_item_id == entry.budget_item_id and 
                            item.due_date == entry.due_date and
                            item.income_date is None):
                            items_to_fix.append({
                                'id': item.id,
                                'income_date': selected_date.isoformat()
                            })
                            break
            
            if not items_to_fix:
                QMessageBox.warning(
                    self, "No Assignments",
                    "Please assign income dates to at least one item."
                )
                return
            
            # Use service to fix unscheduled items (same logic as API!)
            count = self.calendar_service.fix_unscheduled_items(items_to_fix)
            
            dialog.accept()
            
            # Refresh schedule
            self._refresh_schedule()
            
            # Disable button if no more unscheduled items
            if not self.schedule.unscheduled_entries:
                self.fix_unscheduled_button.setEnabled(False)
            
            QMessageBox.information(
                self, "Success",
                f"{count} item(s) have been assigned to income dates!"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save assignments: {str(e)}")

    def set_savings_items(self):
        """Compute and save savings items using service."""
        try:
            # Ask for spending buffer
            spending_buffer, ok = self._ask_spending_buffer()
            if not ok:
                return
            
            # Use service to compute savings (same logic as API!)
            savings_entries = self.calendar_service.compute_savings(
                profile_id=self.selected_profile.id,
                spending_buffer=spending_buffer
            )
            
            if not savings_entries:
                QMessageBox.information(
                    self, "No Savings",
                    "No savings opportunities found with current buffer."
                )
                return
            
            # Show savings dialog
            total = sum(s['amount'] for s in savings_entries)
            msg = f"Found {len(savings_entries)} opportunities totaling ${total:.2f}.\n\nSave them to schedule?"
            
            response = QMessageBox.question(
                self, "Savings Opportunities", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if response == QMessageBox.StandardButton.Yes:
                # Save using service (same logic as API!)
                count = self.calendar_service.save_computed_savings(
                    profile_id=self.selected_profile.id,
                    savings_entries=savings_entries
                )
                
                QMessageBox.information(
                    self, "Success",
                    f"{count} savings items added to schedule."
                )
                
                # Refresh schedule
                self._refresh_schedule()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to compute savings: {str(e)}")
    
    def _ask_spending_buffer(self):
        """Dialog to ask for spending buffer amount."""
        from PyQt6.QtWidgets import QInputDialog
        return QInputDialog.getDouble(
            self, "Spending Buffer",
            "Enter minimum spending buffer amount:",
            400.0, 0.0, 100000.0, 2
        )

    def extrapolate_budget(self, vertical_layout):
        """Run extrapolation using service (same logic as API!)."""
        try:
            # Get date range from UI date pickers
            start_date = self.extrapolation_start_date.date().toPyDate()
            end_date = self.extrapolation_end_date.date().toPyDate()
            
            # Use service to run extrapolation (same logic as API!)
            result = self.calendar_service.run_extrapolation(
                profile_id=self.selected_profile.id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Update schedule from service result
            self.schedule = result['schedule']
            
            # Refresh display
            self.render_schedule(self.schedule_container_layout)
            
            # Enable/disable Fix Unscheduled button based on results
            if result.get('unscheduled_count', 0) > 0:
                self.fix_unscheduled_button.setEnabled(True)
                QMessageBox.warning(
                    self, "Unscheduled Items",
                    f"{result['unscheduled_count']} items could not be scheduled.\n\nUse 'Fix Unscheduled' button to manually assign income dates."
                )
            else:
                self.fix_unscheduled_button.setEnabled(False)
                QMessageBox.information(
                    self, "Success",
                    f"Extrapolation complete! {result['count']} items scheduled."
                )
                
        except Exception as e:
            import traceback
            traceback.print_exc()  # Print full traceback to console for debugging
            QMessageBox.critical(self, "Error", f"Extrapolation failed:\n{str(e)}\n\nCheck console for details.")
    
    def _refresh_schedule(self):
        """Refresh the schedule display."""
        self.schedule.fetch_schedule(self.db, self.selected_profile.id)
        self.schedule.build_schedule()
        self.render_schedule(self.schedule_container_layout)

    def render_schedule(self, vertical_layout):
        self.grid_entries = {}

        # Filter out hidden columns based on profile.hidden_through
        visible_income_dates = []
        for income_date in self.schedule.sorted_income_dates:
            # Skip dates that are hidden (before or equal to hidden_through)
            if self.selected_profile.hidden_through:
                hidden_date = date.fromisoformat(self.selected_profile.hidden_through) if isinstance(self.selected_profile.hidden_through, str) else self.selected_profile.hidden_through
                if income_date <= hidden_date:
                    continue  # Skip this column
            visible_income_dates.append(income_date)
        
        date_strings = []
        for income_date in visible_income_dates:
            date_strings.append(income_date.strftime("%Y-%m-%d"))

        if self.schedule.expense_budget_items is not None and self.schedule_widget is not None:
            vertical_layout.removeWidget(self.schedule_widget)
            del self.schedule_widget

        self.schedule_widget = QTableWidget()
        self.schedule_widget.setColumnCount(len(visible_income_dates))
        self.schedule_widget.setHorizontalHeaderLabels(date_strings)
        # Set fixed column width instead of stretch to prevent super-wide columns
        self.schedule_widget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        # Set reasonable default column width
        for i in range(len(visible_income_dates)):
            self.schedule_widget.setColumnWidth(i, 120)
        self.schedule_widget.horizontalHeader().setStretchLastSection(False)
        # row for each expense plus one for income, a subtotal, and a leftover, and carryover
        self.schedule_widget.setRowCount(len(self.schedule.expense_budget_items) + 4)
        self.schedule_widget.itemClicked.connect(self.cell_clicked)
        
        # Remove dark background - let theme handle it
        self.schedule_widget.setStyleSheet("""
            QTableWidget {
                gridline-color: gray;
            }
        """)

        idx = 0

        # Render carryover row
        self.schedule_widget.setVerticalHeaderItem(idx, QTableWidgetItem("Carryover"))
        cidx = 0
        for income_date in visible_income_dates:
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

            for income_date in visible_income_dates:
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
                    # Handle all income entries in the column
                    if len(schedule_column.incomes) > 0:
                        # Calculate total from all income entries
                        total_income = sum(income.total() for income in schedule_column.incomes)
                        all_incomes_paid = all(income.all_paid() for income in schedule_column.incomes)
                        
                        # Store the first income entry for reference (or could store all)
                        self.grid_entries[(idx, cidx)] = schedule_column.incomes[0]
                        
                        self.schedule_widget.setItem(
                            idx,
                            cidx,
                            self.create_cell(
                                income_date,
                                total_income,
                                True,
                                True,
                                all_incomes_paid,
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

            for income_date in visible_income_dates:
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
        for income_date in visible_income_dates:
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
        for income_date in visible_income_dates:
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
