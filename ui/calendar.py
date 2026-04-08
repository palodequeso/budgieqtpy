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
    QTextEdit,
)
from PyQt6.QtGui import QColor, QBrush, QFont, QPalette
from PyQt6.QtCore import pyqtSlot as Slot, QTimer, QEvent, Qt
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
    QColor("#8B1515"),  # Jan - Red (darker than 900)
    QColor("#6B0A3C"),  # Feb - Pink (darker than 900)
    QColor("#380F6B"),  # Mar - Purple (darker than 900)
    QColor("#9D6A0A"),  # Apr - Yellow/Gold
    QColor("#B84000"),  # May - Orange (darker than 900)
    QColor("#0A3677"),  # Jun - Blue (darker than 900)
    QColor("#014477"),  # Jul - Light Blue (darker than 900)
    QColor("#004D50"),  # Aug - Cyan (darker than 900)
    QColor("#003D32"),  # Sep - Teal (darker than 900)
    QColor("#154718"),  # Oct - Green (darker than 900)
    QColor("#285216"),  # Nov - Light Green (darker than 900)
    QColor("#665E12"),  # Dec - Lime/Olive (darker than 900)
    QColor("#1C262B"),  # neutral (Blue Grey, darker than 900)
    # alt colors (900 shades, second-half-of-month columns)
    QColor("#B71C1C"),  # Jan alt - Red 900
    QColor("#880E4F"),  # Feb alt - Pink 900
    QColor("#4A148C"),  # Mar alt - Purple 900
    QColor("#C67D0D"),  # Apr alt - Yellow/Gold 900
    QColor("#E65100"),  # May alt - Orange 900
    QColor("#0D47A1"),  # Jun alt - Blue 900
    QColor("#01579B"),  # Jul alt - Light Blue 900
    QColor("#006064"),  # Aug alt - Cyan 900
    QColor("#004D40"),  # Sep alt - Teal 900
    QColor("#1B5E20"),  # Oct alt - Green 900
    QColor("#33691E"),  # Nov alt - Light Green 900
    QColor("#827717"),  # Dec alt - Lime 900
    QColor("#263238"),  # neutral alt - Blue Grey 900
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
        self.show_all_columns = False

        self.schedule_vertical_layout = QVBoxLayout()
        self.schedule_vertical_layout.setSpacing(12)
        self.schedule_vertical_layout.setContentsMargins(12, 12, 12, 12)

        # Title section
        title_container = QWidget()
        title_container.setStyleSheet("border-radius: 6px; padding: 12px;")
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        calendar_title = QLabel("Budget Calendar")
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
        extrapolate_button = QPushButton("Extrapolate")
        extrapolate_button.setStyleSheet("""
            QPushButton {
                background-color: #1565c0;
                color: #ffffff;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        extrapolate_button.clicked.connect(
            lambda: self.extrapolate_budget(self.schedule_vertical_layout)
        )
        actions_row.addWidget(extrapolate_button)
        
        # Success action - I Got Paid
        got_paid_button = QPushButton("I Got Paid")
        got_paid_button.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: #ffffff;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
            QPushButton:pressed {
                background-color: #1b5e20;
            }
        """)
        got_paid_button.clicked.connect(self.got_paid)
        actions_row.addWidget(got_paid_button)
        
        # Warning action - Fix Unscheduled
        self.fix_unscheduled_button = QPushButton("Fix Unscheduled")
        self.fix_unscheduled_button.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: #ffffff;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #d32f2f;
            }
            QPushButton:pressed:enabled {
                background-color: #b71c1c;
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
        add_one_off_button = QPushButton("Add One-Off")
        add_one_off_button.setStyleSheet("font-size: 11px; font-weight: bold; padding: 8px 16px;")
        add_one_off_button.clicked.connect(self.add_one_off_entry)
        actions_row.addWidget(add_one_off_button)
        
        add_savings_items_button = QPushButton("Add Savings")
        add_savings_items_button.setStyleSheet("font-size: 11px; font-weight: bold; padding: 8px 16px;")
        add_savings_items_button.clicked.connect(self.set_savings_items)
        actions_row.addWidget(add_savings_items_button)
        
        hide_current_column_button = QPushButton("Hide Column")
        hide_current_column_button.setStyleSheet("font-size: 11px; font-weight: bold; padding: 8px 16px;")
        hide_current_column_button.clicked.connect(self.hide_current_column)
        actions_row.addWidget(hide_current_column_button)

        self.show_hidden_button = QPushButton("Show Hidden")
        self.show_hidden_button.setStyleSheet("font-size: 11px; font-weight: bold; padding: 8px 16px;")
        self.show_hidden_button.clicked.connect(self.toggle_show_hidden)
        self.show_hidden_button.setVisible(bool(self.selected_profile.hidden_through))
        actions_row.addWidget(self.show_hidden_button)

        export_spreadsheet_button = QPushButton("Export")
        export_spreadsheet_button.setStyleSheet("font-size: 11px; font-weight: bold; padding: 8px 16px;")
        export_spreadsheet_button.clicked.connect(self.export_spreadsheet)
        actions_row.addWidget(export_spreadsheet_button)

        ai_analysis_button = QPushButton("AI Analysis")
        ai_analysis_button.setStyleSheet("""
            QPushButton {
                background-color: #6a1b9a;
                color: #ffffff;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
        """)
        ai_analysis_button.clicked.connect(self.run_ai_analysis)
        actions_row.addWidget(ai_analysis_button)

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
        """Color cells by month — matches the web app's logic.
        Regular cells: darker shade (indices 0-11)
        Dull/summary cells: neutral blueGrey (index 12) for Carry/Income/Total rows
        Empty expense cells use the alt shade (indices 13-24) of the month
        """
        colors = MONTH_COLORS_DARK if self.is_dark_mode() else MONTH_COLORS_LIGHT
        month_idx = date.month - 1
        if dull:
            return colors[12]  # Neutral blueGrey for summary rows
        return colors[month_idx]

    def date_to_empty_color(self, date):
        """Color for empty expense cells — brighter alt shade of the month."""
        colors = MONTH_COLORS_DARK if self.is_dark_mode() else MONTH_COLORS_LIGHT
        return colors[(date.month - 1) + 13]

    def format_currency(self, amount):
        return "${:,.2f}".format(amount)
        # return locale.currency(amount, grouping=True)

    def create_cell(self, date, value: float, bold=False, dull=False, paid=False, empty=False):
        out_str = ""
        if value is not None:
            out_str = self.format_currency(value)
        item = QTableWidgetItem(out_str)
        if empty:
            item.setBackground(QBrush(self.date_to_empty_color(date)))
        else:
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

    def run_ai_analysis(self):
        """Run AI analysis on the current budget schedule."""
        from services.ai_service import AIService
        from PyQt6.QtCore import QCoreApplication

        db = Database()
        service = AIService(db)
        config = service.get_config()

        if not config["enabled"] or not config["server_url"]:
            QMessageBox.information(self, "AI Analysis",
                "AI analysis is not configured.\nGo to Settings to set up an AI server URL and model.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("AI Budget Analysis")
        dialog.resize(600, 500)
        layout = QVBoxLayout(dialog)

        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_text.setText("Analyzing your budget...")
        layout.addWidget(result_text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.show()

        # Process events so dialog renders before blocking call
        QCoreApplication.processEvents()

        result = service.analyze(self.selected_profile.id)
        if "error" in result:
            result_text.setText(result["error"])
        else:
            result_text.setMarkdown(result.get("analysis", "No analysis returned"))

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
            layout.addWidget(QLabel(f"\nWarning: {len(unpaid_items)} unpaid item(s) in this column!"))
            layout.addWidget(QLabel("Items will remain in database but hidden from view."))
        else:
            layout.addWidget(QLabel("\nAll items in this column are paid."))
        
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

            # Show the "Show Hidden" button now that hidden_through is set
            self.show_hidden_button.setVisible(True)

            # Refresh schedule (will now filter based on hidden_through)
            self._refresh_schedule()
            
            QMessageBox.information(
                self, "Success",
                f"Columns through {date_key} are now hidden.\n\nTo unhide, adjust the profile's hidden_through date in settings."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to hide column: {str(e)}")

    def toggle_show_hidden(self):
        """Toggle visibility of hidden (past) columns."""
        self.show_all_columns = not self.show_all_columns
        if self.show_all_columns:
            self.show_hidden_button.setText("Hide Past")
        else:
            self.show_hidden_button.setText("Show Hidden")
        self._refresh_schedule()

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
        items_header = QLabel(f"Scheduled Expenses ({len(entry.items)} item{'s' if len(entry.items) != 1 else ''})")
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

            # Name (e.g., debt name for debt payments)
            item_name = getattr(item.extrapolation_item, 'name', None)
            if item_name:
                name_label = QLabel(item_name)
                name_label.setMinimumWidth(100)
                name_label.setStyleSheet("font-size: 11px; font-weight: bold;")
                item_layout.addWidget(name_label)

            # Date
            date_label = QLabel(f"{item.extrapolation_item.due_date.strftime('%Y-%m-%d')}")
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
                paid_label = QLabel("Paid")
                paid_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 12px;")
                item_layout.addWidget(paid_label)
            else:
                btn_style = "font-size: 12px; font-weight: bold; padding: 6px 14px; border: 1px solid #546e7a; border-radius: 4px;"
                mark_paid_button = QPushButton("Mark Paid")
                mark_paid_button.setStyleSheet(btn_style)
                mark_paid_button.clicked.connect(
                    lambda checked=False, i=item, e=entry, d=dialog: self.mark_paid_and_refresh(i, e, d)
                )
                item_layout.addWidget(mark_paid_button)

                move_button = QPushButton("Move")
                move_button.setStyleSheet(btn_style)
                move_button.clicked.connect(
                    lambda checked=False, i=item, e=entry, d=dialog: self._move_single_item(i, e, d)
                )
                item_layout.addWidget(move_button)

                split_button = QPushButton("Split")
                split_button.setStyleSheet(btn_style)
                split_button.clicked.connect(
                    lambda checked=False, i=item, e=entry, d=dialog: self._split_single_item(i, e, d)
                )
                item_layout.addWidget(split_button)

            item_container.setLayout(item_layout)
            scroll_layout.addWidget(item_container)
        
        scroll_layout.addStretch(1)
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        close_button = QPushButton("Close")
        close_button.setStyleSheet("font-size: 12px; font-weight: bold; padding: 8px 24px;")
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

    def _move_single_item(self, item, entry, parent_dialog):
        """Move a single extrapolation item to a different income column from the entry detail dialog."""
        input_style = "padding: 10px; font-size: 14px;"
        label_font = QFont()
        label_font.setPointSize(11)
        label_font.setBold(True)
        btn_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"

        dialog = QDialog(self)
        dialog.setWindowTitle("Move Item")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 16)

        info = QLabel(f"Move '{entry.budget_item.name}' (${abs(item.extrapolation_item.amount):,.2f})")
        info.setFont(label_font)
        info.setWordWrap(True)
        layout.addWidget(info)

        from_label = QLabel(f"From: {entry.income_date.strftime('%Y-%m-%d')}")
        from_label.setStyleSheet("font-size: 13px; color: #90a4ae;")
        layout.addWidget(from_label)
        layout.addSpacing(8)

        dest_label = QLabel("Move to")
        dest_label.setFont(label_font)
        layout.addWidget(dest_label)

        dest_combo = QComboBox()
        dest_combo.setStyleSheet(input_style)
        dest_combo.setMinimumHeight(40)
        current_date_str = entry.income_date.strftime("%Y-%m-%d")
        for inc_date in self.schedule.sorted_income_dates:
            ds = inc_date.strftime("%Y-%m-%d")
            if ds != current_date_str:
                col = self.schedule.columns.get(inc_date)
                balance = col.total() if col else 0
                dest_combo.addItem(f"{ds}  (balance: ${balance:,.2f})", ds)
        layout.addWidget(dest_combo)
        layout.addSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(btn_style)
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        move_btn = QPushButton("Move")
        move_btn.setStyleSheet(btn_style)
        move_btn.setMinimumHeight(40)
        btn_row.addWidget(move_btn)
        layout.addLayout(btn_row)

        def do_move():
            to_date = dest_combo.currentData()
            if not to_date:
                return
            try:
                self.db.move_extrapolation_items(
                    self.selected_profile.id, entry.budget_item.id,
                    current_date_str, to_date
                )
                dialog.accept()
                parent_dialog.accept()
                QMessageBox.information(self, "Moved", f"Item moved to {to_date}.")
                self._refresh_schedule()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to move: {str(e)}")

        move_btn.clicked.connect(do_move)
        dialog.setLayout(layout)
        dialog.exec()

    def _split_single_item(self, item, entry, parent_dialog):
        """Split a single extrapolation item from the entry detail dialog."""
        input_style = "padding: 10px; font-size: 14px;"
        label_font = QFont()
        label_font.setPointSize(11)
        label_font.setBold(True)
        btn_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"

        total_amount = abs(float(item.extrapolation_item.amount))
        item_id = item.extrapolation_item.id

        dialog = QDialog(self)
        dialog.setWindowTitle("Split Item")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 16)

        info = QLabel(f"Split '{entry.budget_item.name}'")
        info.setFont(label_font)
        layout.addWidget(info)

        total_lbl = QLabel(f"Total: ${total_amount:,.2f}")
        total_lbl.setStyleSheet("font-size: 13px; color: #90a4ae;")
        layout.addWidget(total_lbl)
        layout.addSpacing(8)

        keep_label = QLabel("Amount to keep in this period")
        keep_label.setFont(label_font)
        layout.addWidget(keep_label)

        keep_input = QLineEdit(f"{total_amount / 2:.2f}")
        keep_input.setStyleSheet(input_style)
        keep_input.setMinimumHeight(40)
        layout.addWidget(keep_input)

        remainder_label = QLabel(f"Remainder: ${total_amount / 2:,.2f}")
        remainder_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(remainder_label)

        def update_remainder():
            try:
                keep = float(keep_input.text())
                rem = total_amount - keep
                remainder_label.setText(f"Remainder: ${rem:,.2f}")
                if rem <= 0 or keep <= 0:
                    remainder_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #ef5350;")
                else:
                    remainder_label.setStyleSheet("font-size: 13px; font-weight: bold;")
            except ValueError:
                remainder_label.setText("Remainder: --")

        keep_input.textChanged.connect(update_remainder)
        layout.addSpacing(8)

        dest_label = QLabel("Move remainder to")
        dest_label.setFont(label_font)
        layout.addWidget(dest_label)

        dest_combo = QComboBox()
        dest_combo.setStyleSheet(input_style)
        dest_combo.setMinimumHeight(40)
        current_date_str = entry.income_date.strftime("%Y-%m-%d")
        dest_combo.addItem(f"{current_date_str}  (same column)", current_date_str)
        for inc_date in self.schedule.sorted_income_dates:
            ds = inc_date.strftime("%Y-%m-%d")
            if ds != current_date_str:
                dest_combo.addItem(ds, ds)
        layout.addWidget(dest_combo)
        layout.addSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(btn_style)
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        split_btn = QPushButton("Split")
        split_btn.setStyleSheet(btn_style)
        split_btn.setMinimumHeight(40)
        btn_row.addWidget(split_btn)
        layout.addLayout(btn_row)

        def do_split():
            try:
                keep = float(keep_input.text())
            except ValueError:
                QMessageBox.warning(dialog, "Invalid", "Enter a valid amount.")
                return
            if keep <= 0 or keep >= total_amount:
                QMessageBox.warning(dialog, "Invalid", "Keep amount must be between 0 and the total.")
                return

            remainder_date = dest_combo.currentData()
            try:
                self.db.split_extrapolation_item(item_id, keep, remainder_date)
                dialog.accept()
                parent_dialog.accept()
                QMessageBox.information(self, "Split", f"Item split: ${keep:,.2f} kept, ${total_amount - keep:,.2f} moved to {remainder_date}.")
                self._refresh_schedule()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to split: {str(e)}")

        split_btn.clicked.connect(do_split)
        dialog.setLayout(layout)
        dialog.exec()

    def got_paid(self):
        accounts = self.db.fetch_accounts(self.selected_profile.id)

        got_paid_dialog = QDialog()
        got_paid_dialog.setWindowTitle("Got Paid")
        got_paid_dialog.setMinimumWidth(400)
        got_paid_layout = QVBoxLayout()
        got_paid_layout.setSpacing(12)
        got_paid_layout.setContentsMargins(20, 20, 20, 16)

        field_label_font = QFont()
        field_label_font.setPointSize(11)
        field_label_font.setBold(True)

        input_style = "padding: 10px; font-size: 14px;"
        button_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"

        dialog_label = QLabel("Hooray, it's payday!")
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

        got_paid_layout.addSpacing(8)

        # Income date selection
        date_label = QLabel("Income Date")
        date_label.setFont(field_label_font)
        got_paid_layout.addWidget(date_label)

        income_date_selector = QComboBox()
        income_date_selector.addItems(
            [x.strftime("%Y-%m-%d") for x in unpaid_income_dates]
        )
        income_date_selector.setStyleSheet(input_style)
        income_date_selector.setMinimumHeight(40)
        got_paid_layout.addWidget(income_date_selector)

        got_paid_layout.addSpacing(8)

        # Account selection
        account_label = QLabel("Deposit to Account")
        account_label.setFont(field_label_font)
        got_paid_layout.addWidget(account_label)

        account_selector = QComboBox()
        for account in accounts:
            account_selector.addItem(account.name)
        account_selector.setStyleSheet(input_style)
        account_selector.setMinimumHeight(40)
        got_paid_layout.addWidget(account_selector)

        got_paid_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(button_style)
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(lambda: got_paid_dialog.close())
        buttons_layout.addWidget(cancel_button)

        save_button = QPushButton("Mark as Received")
        save_button.setStyleSheet(button_style)
        save_button.setMinimumHeight(40)
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
        mark_paid_layout.setContentsMargins(20, 20, 20, 16)

        field_label_font = QFont()
        field_label_font.setPointSize(11)
        field_label_font.setBold(True)

        input_style = "padding: 10px; font-size: 14px;"
        button_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"

        # Header section
        header_widget = QWidget()
        header_widget.setStyleSheet("padding: 12px; border-radius: 6px;")
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        name_label = QLabel(entry.budget_item.name)
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        name_label.setFont(name_font)
        header_layout.addWidget(name_label)

        type_label = QLabel(f"Type: {entry.budget_item.type}")
        type_label.setStyleSheet("font-size: 13px;")
        header_layout.addWidget(type_label)

        income_date_label = QLabel(f"Income Date: {entry.income_date.strftime('%Y-%m-%d')}")
        income_date_label.setStyleSheet("font-size: 13px;")
        header_layout.addWidget(income_date_label)

        due_date_label = QLabel(f"Due Date: {item.extrapolation_item.due_date.strftime('%Y-%m-%d')}")
        due_date_label.setStyleSheet("color: #3498db; font-size: 13px; font-weight: bold;")
        header_layout.addWidget(due_date_label)

        header_widget.setLayout(header_layout)
        mark_paid_layout.addWidget(header_widget)

        mark_paid_layout.addSpacing(8)

        # Account selection
        account_label = QLabel("Account")
        account_label.setFont(field_label_font)
        mark_paid_layout.addWidget(account_label)

        account_help = QLabel("Which account was this paid from?")
        account_help.setStyleSheet("font-size: 13px; font-style: italic;")
        mark_paid_layout.addWidget(account_help)

        account_combobox = QComboBox()
        for account in accounts:
            account_combobox.addItem(account.name)
        account_combobox.setStyleSheet(input_style)
        account_combobox.setMinimumHeight(40)
        mark_paid_layout.addWidget(account_combobox)

        mark_paid_layout.addSpacing(8)

        # Amount
        amount_label = QLabel("Actual Paid Amount")
        amount_label.setFont(field_label_font)
        mark_paid_layout.addWidget(amount_label)

        paid_amount_widget = QLineEdit()
        paid_amount_widget.setText(str(item.extrapolation_item.amount))
        paid_amount_widget.setStyleSheet(input_style)
        paid_amount_widget.setMinimumHeight(40)
        mark_paid_layout.addWidget(paid_amount_widget)

        mark_paid_layout.addSpacing(8)

        # Date
        date_label = QLabel("Actual Paid Date")
        date_label.setFont(field_label_font)
        mark_paid_layout.addWidget(date_label)

        paid_date_widget = QDateEdit()
        paid_date_widget.setDate(date.today())
        paid_date_widget.setCalendarPopup(True)
        paid_date_widget.setStyleSheet(input_style)
        paid_date_widget.setMinimumHeight(40)
        mark_paid_layout.addWidget(paid_date_widget)

        mark_paid_layout.addStretch(1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(button_style)
        cancel_button.setMinimumHeight(40)
        buttons_layout.addWidget(cancel_button)
        cancel_button.clicked.connect(lambda: mark_paid_dialog.close())

        ok_button = QPushButton("Save Payment")
        ok_button.setStyleSheet(button_style)
        ok_button.setMinimumHeight(40)
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
    
    @Slot(QTableWidgetItem)
    def cell_clicked(self, item):
        entry = self.grid_entries.get((item.row(), item.column()), None)
        if entry is None:
            return

        self.select_entry(entry)

    def _quick_mark_paid(self, row, col):
        """Double-click handler: quickly mark a single unpaid expense item as paid."""
        entry = self.grid_entries.get((row, col), None)
        if entry is None or not entry.items:
            return

        unpaid_items = [item for item in entry.items if item.ledger_entry is None]
        if not unpaid_items:
            return  # Everything already paid

        if len(unpaid_items) == 1:
            # Exactly one unpaid item -- quick-pay with first available account
            item = unpaid_items[0]
            accounts = self.db.fetch_accounts(self.selected_profile.id)
            if not accounts:
                QMessageBox.warning(self, "No Accounts", "No accounts available to record payment.")
                return

            reply = QMessageBox.question(
                self,
                "Quick Mark Paid",
                f"Mark '{entry.budget_item.name}' (${abs(item.extrapolation_item.amount):,.2f}) as paid?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            try:
                self.ledger_service.mark_extrapolation_item_paid(
                    extrapolation_item_id=item.extrapolation_item.id,
                    account_id=accounts[0].id,
                    paid_date=date.today().isoformat(),
                )
                QMessageBox.information(self, "Paid", f"'{entry.budget_item.name}' marked as paid.")
                QTimer.singleShot(100, self._refresh_schedule)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to mark paid: {str(e)}")
        else:
            # Multiple unpaid items -- open the detail dialog so user can choose
            self.select_entry(entry)

    def add_one_off_entry(self):
        one_off_dialog = QDialog()
        one_off_dialog.setWindowTitle("Add One-Off Entry")
        one_off_dialog.setMinimumWidth(450)
        one_off_layout = QVBoxLayout()
        one_off_layout.setSpacing(12)
        one_off_layout.setContentsMargins(20, 20, 20, 16)

        field_label_font = QFont()
        field_label_font.setPointSize(11)
        field_label_font.setBold(True)

        input_style = "padding: 10px; font-size: 14px;"
        button_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"

        # Header
        header_label = QLabel("Add One-Off Entry")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setStyleSheet("margin-bottom: 8px;")
        one_off_layout.addWidget(header_label)

        desc_label = QLabel("Create a single non-recurring budget entry")
        desc_label.setStyleSheet("font-size: 13px; margin-bottom: 8px;")
        one_off_layout.addWidget(desc_label)

        one_off_layout.addSpacing(8)

        # Name
        name_label = QLabel("Name")
        name_label.setFont(field_label_font)
        one_off_layout.addWidget(name_label)

        name_widget = QLineEdit()
        name_widget.setPlaceholderText("e.g., Car Repair")
        name_widget.setStyleSheet(input_style)
        name_widget.setMinimumHeight(40)
        one_off_layout.addWidget(name_widget)

        one_off_layout.addSpacing(8)

        # Amount
        amount_label = QLabel("Amount")
        amount_label.setFont(field_label_font)
        one_off_layout.addWidget(amount_label)

        amount_widget = QLineEdit('0.00')
        amount_widget.setStyleSheet(input_style)
        amount_widget.setMinimumHeight(40)
        one_off_layout.addWidget(amount_widget)

        one_off_layout.addSpacing(8)

        # Type
        type_label = QLabel("Type")
        type_label.setFont(field_label_font)
        one_off_layout.addWidget(type_label)

        type_widget = QComboBox()
        type_widget.addItem("Expense")
        type_widget.addItem("Income")
        type_widget.setStyleSheet(input_style)
        type_widget.setMinimumHeight(40)
        one_off_layout.addWidget(type_widget)

        one_off_layout.addSpacing(8)

        # Due Date
        date_label = QLabel("Due Date")
        date_label.setFont(field_label_font)
        one_off_layout.addWidget(date_label)

        date_widget = QDateEdit(date.today())
        date_widget.setCalendarPopup(True)
        date_widget.setStyleSheet(input_style)
        date_widget.setMinimumHeight(40)
        one_off_layout.addWidget(date_widget)

        one_off_layout.addSpacing(8)

        # Income Date
        income_date_label = QLabel("Income Date")
        income_date_label.setFont(field_label_font)
        one_off_layout.addWidget(income_date_label)

        income_date_widget = QComboBox()
        income_date_widget.addItems([x.strftime("%Y-%m-%d") for x in self.schedule.sorted_income_dates])
        income_date_widget.setStyleSheet(input_style)
        income_date_widget.setMinimumHeight(40)
        one_off_layout.addWidget(income_date_widget)

        one_off_layout.addSpacing(8)

        # Paid checkbox
        paid_widget = QCheckBox("Mark as already paid")
        paid_widget.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                margin-top: 8px;
            }
        """)
        one_off_layout.addWidget(paid_widget)

        one_off_layout.addSpacing(8)

        # Account (only enabled if paid)
        account_label = QLabel("Account")
        account_label.setFont(field_label_font)
        one_off_layout.addWidget(account_label)

        account_widget = QComboBox()
        accounts = self.db.fetch_accounts(self.selected_profile.id)
        for account in accounts:
            account_widget.addItem(account.name)
        account_widget.setEnabled(False)
        account_widget.setStyleSheet(input_style)
        account_widget.setMinimumHeight(40)
        paid_widget.checkStateChanged.connect(lambda: account_widget.setEnabled(paid_widget.isChecked()))
        one_off_layout.addWidget(account_widget)

        one_off_layout.addStretch(1)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(button_style)
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(lambda: one_off_dialog.close())
        buttons_layout.addWidget(cancel_button)

        ok_button = QPushButton("Save Entry")
        ok_button.setStyleSheet(button_style)
        ok_button.setMinimumHeight(40)
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
        layout.setContentsMargins(20, 20, 20, 16)

        # Header
        header_label = QLabel(f"Fix Unscheduled Items")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setStyleSheet("margin-bottom: 4px;")
        layout.addWidget(header_label)

        desc_label = QLabel(f"{len(self.schedule.unscheduled_entries)} item(s) could not be automatically scheduled. Manually assign an income date to each item:")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 13px; margin-bottom: 8px;")
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
            info_label = QLabel(f"{entry.name} - {self.format_currency(entry.amount)} (Due: {entry.due_date.strftime('%Y-%m-%d')})")
            info_label.setMinimumWidth(320)
            info_label.setStyleSheet("font-size: 13px; font-weight: 500;")
            item_layout.addWidget(info_label)

            # Income date picker
            income_date_combo = QComboBox()
            income_date_combo.addItem("-- Select Income Date --", None)
            for income_date in self.schedule.sorted_income_dates:
                income_date_combo.addItem(
                    income_date.strftime("%Y-%m-%d"),
                    income_date
                )
            income_date_combo.setStyleSheet("padding: 10px; font-size: 14px; min-width: 140px;")
            income_date_combo.setMinimumHeight(40)
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
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;")
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)

        save_button = QPushButton("Save Assignments")
        save_button.setStyleSheet("padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;")
        save_button.setMinimumHeight(40)
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
        dialog = QDialog(self)
        dialog.setWindowTitle("Spending Buffer")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 16)

        field_label_font = QFont()
        field_label_font.setPointSize(11)
        field_label_font.setBold(True)

        prompt_label = QLabel("Enter minimum spending buffer amount:")
        prompt_label.setFont(field_label_font)
        layout.addWidget(prompt_label)

        help_label = QLabel("This is the minimum amount to keep available for spending each pay period.")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("font-size: 13px; font-style: italic;")
        layout.addWidget(help_label)

        layout.addSpacing(8)

        amount_input = QLineEdit("400.00")
        amount_input.setStyleSheet("padding: 10px; font-size: 14px;")
        amount_input.setMinimumHeight(40)
        layout.addWidget(amount_input)

        layout.addStretch(1)

        button_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(button_style)
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)

        ok_button = QPushButton("OK")
        ok_button.setStyleSheet(button_style)
        ok_button.setMinimumHeight(40)
        ok_button.clicked.connect(dialog.accept)
        buttons_layout.addWidget(ok_button)

        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            try:
                return float(amount_input.text()), True
            except ValueError:
                return 400.0, True
        return 0.0, False

    def extrapolate_budget(self, vertical_layout):
        """Run extrapolation using service (same logic as API!)."""
        confirm = QMessageBox.question(
            self,
            "Run Budget Extrapolation?",
            "Extrapolation schedules your recurring budget items across the date range "
            "you've selected. Here's how it works:\n\n"
            "\u2022 Your income items become columns in the schedule \u2014 one column per payday\n"
            "\u2022 Expenses are placed into the earliest column that can cover them\n"
            "\u2022 If an expense can't fit anywhere, it's marked as unscheduled for you to handle manually\n"
            "\u2022 Items you've already marked as paid are preserved\n\n"
            "After extrapolation, take a moment to review the results. The scheduling "
            "algorithm does its best, but you know your finances better than any algorithm.\n\n"
            "Once your schedule looks right, consider adding savings items to start "
            "building a safety net \u2014 even small amounts add up.\n\n"
            "You've got this!",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Ok
        )
        if confirm != QMessageBox.StandardButton.Ok:
            return
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
            if not self.show_all_columns and self.selected_profile.hidden_through:
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

        # Determine which column contains "today" for the today-indicator
        today = date.today()
        today_col_idx = None
        if visible_income_dates:
            # Find the last income_date that is <= today
            for i, inc_date in enumerate(visible_income_dates):
                if inc_date <= today:
                    today_col_idx = i
            # If today is before all dates, highlight the first column
            if today_col_idx is None:
                today_col_idx = 0

        # Set column headers, marking "today" column with a prefix
        header_labels = []
        for i, ds in enumerate(date_strings):
            if i == today_col_idx:
                header_labels.append(f"\u25b8 {ds}")
            else:
                header_labels.append(ds)
        self.schedule_widget.setHorizontalHeaderLabels(header_labels)

        # Bold the "today" column header
        if today_col_idx is not None:
            header_item = self.schedule_widget.horizontalHeaderItem(today_col_idx)
            if header_item:
                bold_font = QFont()
                bold_font.setBold(True)
                header_item.setFont(bold_font)

        # Set fixed column width instead of stretch to prevent super-wide columns
        self.schedule_widget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        # Set reasonable default column width
        for i in range(len(visible_income_dates)):
            self.schedule_widget.setColumnWidth(i, 120)
        self.schedule_widget.horizontalHeader().setStretchLastSection(False)
        # rows: carryover + each income + each expense + subtotal + leftover + safe-to-spend
        self.schedule_widget.setRowCount(
            1 + len(self.schedule.income_budget_items) + len(self.schedule.expense_budget_items) + 3
        )
        self.schedule_widget.itemClicked.connect(self.cell_clicked)
        self.schedule_widget.cellDoubleClicked.connect(self._quick_mark_paid)
        # Context menu removed — use the cell detail dialog for Move/Split per-item

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

        # Render income rows (one per income budget item)
        for budget_item in self.schedule.income_budget_items:
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

                # Find matching income entry for this budget item
                matching = next(
                    (e for e in schedule_column.incomes if e.budget_item.id == budget_item.id),
                    None,
                )
                if matching is not None:
                    self.grid_entries[(idx, cidx)] = matching
                    self.schedule_widget.setItem(
                        idx,
                        cidx,
                        self.create_cell(
                            income_date,
                            matching.total(),
                            True,
                            True,
                            matching.all_paid(),
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
                        idx, cidx, self.create_cell(income_date, None, empty=True)
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
                if matching is not None:
                    self.grid_entries[(idx, cidx)] = matching
                    cell_item = self.create_cell(
                        income_date,
                        matching.total(),
                        False,
                        False,
                        matching.all_paid(),
                    )
                    # Overdue highlighting: red tint for unpaid expenses past their income date
                    if income_date < date.today() and not matching.all_paid():
                        overdue_bg = QColor("#4a1a1a") if self.is_dark_mode() else QColor("#ffcdd2")
                        cell_item.setBackground(QBrush(overdue_bg))
                        if self.is_dark_mode():
                            cell_item.setForeground(QBrush(QColor("#ff8a80")))
                    cell_item.setData(Qt.ItemDataRole.UserRole, {
                        'budget_item_id': budget_item.id,
                        'income_date': income_date.strftime("%Y-%m-%d"),
                    })
                    self.schedule_widget.setItem(idx, cidx, cell_item)
                else:
                    self.schedule_widget.setItem(
                        idx, cidx, self.create_cell(income_date, None, empty=True)
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

        # Render safe to spend row
        self.schedule_widget.setVerticalHeaderItem(idx, QTableWidgetItem("Safe to Spend"))
        cidx = 0
        for income_date in visible_income_dates:
            schedule_column = self.schedule.columns.get(
                income_date.strftime("%Y-%m-%d"), None
            )
            if schedule_column is not None:
                safe = schedule_column.income_total() + schedule_column.expenses_total()
                cell = self.create_cell(income_date, safe, True, True)
                safe_color = QColor("#4caf50") if safe >= 0 else QColor("#ef5350")
                cell.setForeground(QBrush(safe_color))
                self.schedule_widget.setItem(idx, cidx, cell)
            cidx += 1
        idx += 1

        vertical_layout.addWidget(self.schedule_widget)

        # Auto-scroll to the "today" column
        if today_col_idx is not None and self.schedule_widget.rowCount() > 0:
            target_item = self.schedule_widget.item(0, today_col_idx)
            if target_item:
                self.schedule_widget.scrollToItem(
                    target_item, QTableWidget.ScrollHint.PositionAtCenter
                )
