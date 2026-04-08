from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QStackedWidget,
    QMessageBox,
    QLabel,
    QHeaderView,
    QComboBox,
    QFileDialog,
    QScrollArea,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database.database import Database
from database.profile import Profile
from services.reconciliation_service import ReconciliationService
from ui.onboarding import HelpIcon, HELP_TEXTS


class Reconcile(QStackedWidget):
    db: Database = None
    selected_profile: Profile = None
    csv_content: str = None
    csv_filename: str = None
    match_results: list = None

    def __init__(self, db, selected_profile):
        super().__init__()
        self.db = db
        self.selected_profile = selected_profile
        self.csv_content = None
        self.csv_filename = None
        self.match_results = []
        self.service = ReconciliationService(db)
        self.render_upload()
        self.render_review_placeholder()

    def _clear_all_widgets(self):
        while self.count() > 0:
            w = self.widget(0)
            self.removeWidget(w)
            w.deleteLater()

    # ── View 1: Upload & Parse ──────────────────────────────────────────

    def render_upload(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vl = QVBoxLayout(container)
        vl.setSpacing(12)
        vl.setContentsMargins(20, 20, 20, 20)

        title_row = QHBoxLayout()
        title = QLabel("Bank Reconciliation")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title_row.addWidget(title)
        title_row.addWidget(HelpIcon(HELP_TEXTS["reconcile"]))
        title_row.addStretch(1)
        vl.addLayout(title_row)

        description = QLabel(
            "Import a bank CSV file to match transactions against your budget.\n"
            "This helps you verify that your actual spending matches what you planned."
        )
        description.setStyleSheet("color: #999; padding-bottom: 10px;")
        vl.addWidget(description)

        # CSV file selection
        file_row = QHBoxLayout()
        select_btn = QPushButton("Select CSV File")
        select_btn.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        select_btn.clicked.connect(self._select_csv_file)
        file_row.addWidget(select_btn)

        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #999; padding-left: 10px;")
        file_row.addWidget(self.file_label)
        file_row.addStretch(1)
        vl.addLayout(file_row)

        # Account selection
        vl.addWidget(QLabel("Account:"))
        self.account_combo = QComboBox()
        self.accounts = self.db.fetch_accounts(self.selected_profile.id)
        for account in self.accounts:
            self.account_combo.addItem(account.name, account.id)
        vl.addWidget(self.account_combo)

        # Optional column mapping
        mapping_label = QLabel("Column Mapping (leave blank for auto-detection):")
        mapping_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        vl.addWidget(mapping_label)

        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Date Column:"))
        self.date_col_input = QLineEdit()
        self.date_col_input.setPlaceholderText("auto-detect")
        date_row.addWidget(self.date_col_input)
        vl.addLayout(date_row)

        amount_row = QHBoxLayout()
        amount_row.addWidget(QLabel("Amount Column:"))
        self.amount_col_input = QLineEdit()
        self.amount_col_input.setPlaceholderText("auto-detect")
        amount_row.addWidget(self.amount_col_input)
        vl.addLayout(amount_row)

        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel("Description Column:"))
        self.desc_col_input = QLineEdit()
        self.desc_col_input.setPlaceholderText("auto-detect")
        desc_row.addWidget(self.desc_col_input)
        vl.addLayout(desc_row)

        # Parse button
        parse_btn = QPushButton("Parse && Match")
        parse_btn.setStyleSheet("font-weight: bold; padding: 10px 20px; margin-top: 10px;")
        parse_btn.clicked.connect(self._parse_and_match)
        vl.addWidget(parse_btn)

        vl.addStretch(1)
        scroll.setWidget(container)
        self.addWidget(scroll)

    def render_review_placeholder(self):
        """Add an empty placeholder for View 2 so the stacked widget has two indices."""
        placeholder = QWidget()
        self.addWidget(placeholder)

    def _select_csv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.csv_content = f.read()
                self.csv_filename = file_path.split("/")[-1]
                self.file_label.setText(self.csv_filename)
                self.file_label.setStyleSheet("color: #27ae60; padding-left: 10px;")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read file: {str(e)}")

    def _parse_and_match(self):
        if not self.csv_content:
            QMessageBox.warning(self, "No File", "Please select a CSV file first.")
            return

        if self.account_combo.count() == 0:
            QMessageBox.warning(self, "No Account", "Please create an account first.")
            return

        account_id = self.account_combo.currentData()

        # Get optional column overrides (empty string -> None for auto-detect)
        date_col = self.date_col_input.text().strip() or None
        amount_col = self.amount_col_input.text().strip() or None
        desc_col = self.desc_col_input.text().strip() or None

        try:
            parsed = self.service.parse_csv(
                self.csv_content,
                date_col=date_col,
                amount_col=amount_col,
                desc_col=desc_col,
            )

            if parsed["count"] == 0:
                QMessageBox.warning(
                    self, "No Transactions",
                    "No valid transactions were found in the CSV file."
                )
                return

            self.match_results = self.service.match_transactions(
                self.selected_profile.id,
                parsed["transactions"],
                account_id,
            )

            self._render_review()
            self.setCurrentIndex(1)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse CSV: {str(e)}")

    # ── View 2: Review & Import ─────────────────────────────────────────

    def _render_review(self):
        # Remove old review widget and add fresh one
        old = self.widget(1)
        if old:
            self.removeWidget(old)
            old.deleteLater()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vl = QVBoxLayout(container)
        vl.setSpacing(12)
        vl.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Review Matches")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        vl.addWidget(title)

        summary_text = (
            f"Found {len(self.match_results)} transaction(s). "
            f"Matched: {sum(1 for r in self.match_results if r['status'] == 'matched')}, "
            f"Unmatched: {sum(1 for r in self.match_results if r['status'] == 'unmatched')}."
        )
        summary = QLabel(summary_text)
        summary.setStyleSheet("color: #999; padding-bottom: 10px;")
        vl.addWidget(summary)

        # Results table
        self.review_table = QTableWidget()
        self.review_table.setColumnCount(7)
        self.review_table.setHorizontalHeaderLabels([
            "Include", "Status", "Date", "Amount", "Description", "Matched To", "Confidence"
        ])
        self.review_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self.review_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch
        )
        self.review_table.setRowCount(len(self.match_results))

        self.review_table.setStyleSheet("""
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

        for row, result in enumerate(self.match_results):
            txn = result["transaction"]
            match = result["match"]
            is_matched = result["status"] == "matched"

            # Include checkbox
            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            check_item.setCheckState(
                Qt.CheckState.Checked if is_matched else Qt.CheckState.Unchecked
            )
            self.review_table.setItem(row, 0, check_item)

            # Status
            status_item = QTableWidgetItem("Matched" if is_matched else "Unmatched")
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if is_matched:
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.yellow)
            self.review_table.setItem(row, 1, status_item)

            # Date
            date_item = QTableWidgetItem(txn["date"])
            date_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.review_table.setItem(row, 2, date_item)

            # Amount (editable)
            amount_item = QTableWidgetItem(f"{txn['amount']:.2f}")
            amount_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
            )
            self.review_table.setItem(row, 3, amount_item)

            # Description
            desc_item = QTableWidgetItem(txn["description"])
            desc_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.review_table.setItem(row, 4, desc_item)

            # Matched To
            matched_text = match["budget_item_name"] if match else ""
            matched_item = QTableWidgetItem(matched_text)
            matched_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.review_table.setItem(row, 5, matched_item)

            # Confidence
            confidence_text = f"{match['confidence']}%" if match else ""
            confidence_item = QTableWidgetItem(confidence_text)
            confidence_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.review_table.setItem(row, 6, confidence_item)

            self.review_table.setRowHeight(row, 40)

        vl.addWidget(self.review_table)

        # Buttons
        btn_row = QHBoxLayout()

        back_btn = QPushButton("Back")
        back_btn.setStyleSheet("padding: 8px 16px;")
        back_btn.clicked.connect(lambda: self.setCurrentIndex(0))
        btn_row.addWidget(back_btn)

        btn_row.addStretch(1)

        import_btn = QPushButton("Import Selected")
        import_btn.setStyleSheet("font-weight: bold; padding: 10px 20px;")
        import_btn.clicked.connect(self._import_selected)
        btn_row.addWidget(import_btn)

        vl.addLayout(btn_row)
        vl.addStretch(1)

        scroll.setWidget(container)
        self.addWidget(scroll)

    def _import_selected(self):
        account_id = self.account_combo.currentData()
        confirmed = []

        for row in range(self.review_table.rowCount()):
            check_item = self.review_table.item(row, 0)
            if check_item.checkState() != Qt.CheckState.Checked:
                continue

            result = self.match_results[row]
            txn = result["transaction"]
            match = result["match"]

            # Read potentially overridden amount
            amount_text = self.review_table.item(row, 3).text()
            try:
                override_amount = float(amount_text)
            except ValueError:
                override_amount = txn["amount"]

            # Determine if amount was changed
            amount_override = None
            if abs(override_amount - txn["amount"]) > 0.001:
                amount_override = override_amount

            confirmed.append({
                "transaction": txn,
                "extrapolation_item_id": match["extrapolation_item_id"] if match else None,
                "amount_override": amount_override,
            })

        if not confirmed:
            QMessageBox.warning(
                self, "Nothing Selected",
                "No transactions are selected for import."
            )
            return

        try:
            result = self.service.import_confirmed(
                self.selected_profile.id, account_id, confirmed
            )
            QMessageBox.information(
                self, "Import Complete",
                f"Imported {result['imported']} transaction(s).\n"
                f"Linked {result['linked']} to existing budget items."
            )
            # Reset back to upload view
            self._clear_all_widgets()
            self.csv_content = None
            self.csv_filename = None
            self.match_results = []
            self.render_upload()
            self.render_review_placeholder()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")
