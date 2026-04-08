import json
import os
import platform
import subprocess
import sys
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QFileDialog,
)
from database.database import Database
from database.profile import Profile
from ui.onboarding import OnboardingWizard


class Settings(QDialog):
    layout: QVBoxLayout = None
    db: Database = None
    selected_profile: Profile = None

    def __init__(self, db: Database = None, selected_profile: Profile = None):
        super().__init__()
        self.db = db
        self.selected_profile = selected_profile
        self.render_settings()

    def render_settings(self):
        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(24, 20, 24, 16)
        self.setLayout(layout)

        from PyQt6.QtGui import QFont
        input_style = "padding: 10px; font-size: 14px;"
        input_height = 40
        section_font = QFont()
        section_font.setPointSize(13)
        section_font.setBold(True)
        label_font = QFont()
        label_font.setPointSize(11)
        label_font.setBold(True)
        btn_style = "padding: 10px 20px; border: 1px solid #546e7a; border-radius: 5px; font-size: 13px; font-weight: bold;"

        def section_label(text):
            lbl = QLabel(text)
            lbl.setFont(section_font)
            return lbl

        def field_label(text):
            lbl = QLabel(text)
            lbl.setFont(label_font)
            return lbl

        # ── Theme ──
        if self.db and self.selected_profile:
            layout.addWidget(section_label("Theme"))
            layout.addSpacing(4)

            self.theme_combo = QComboBox()
            self.theme_combo.addItem("Dark", "dark")
            self.theme_combo.addItem("Light", "light")
            current_theme = self.selected_profile.theme if self.selected_profile.theme else "dark"
            self.theme_combo.setCurrentIndex(0 if current_theme == "dark" else 1)
            self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
            self.theme_combo.setStyleSheet(input_style)
            self.theme_combo.setMinimumHeight(input_height)
            layout.addWidget(self.theme_combo)
            layout.addSpacing(16)

        # ── Spreadsheet Export ──
        layout.addWidget(section_label("Spreadsheet Export"))
        layout.addSpacing(4)

        layout.addWidget(field_label("Backup Location"))
        backup_row = QHBoxLayout()
        backup_row.setSpacing(8)
        spreadsheet_backup_location_widget = QLineEdit('./schedule-spreadsheets/')
        spreadsheet_backup_location_widget.setStyleSheet(input_style)
        spreadsheet_backup_location_widget.setMinimumHeight(input_height)
        backup_row.addWidget(spreadsheet_backup_location_widget)
        open_location_button = QPushButton("Open")
        open_location_button.setStyleSheet(btn_style)
        open_location_button.setMinimumHeight(input_height)
        open_location_button.clicked.connect(
            lambda: self.open_location(spreadsheet_backup_location_widget.text())
        )
        backup_row.addWidget(open_location_button)
        layout.addLayout(backup_row)
        layout.addSpacing(8)

        layout.addWidget(field_label("Max Backups"))
        spreadsheet_backup_count_widget = QLineEdit('5000')
        spreadsheet_backup_count_widget.setStyleSheet(input_style)
        spreadsheet_backup_count_widget.setMinimumHeight(input_height)
        spreadsheet_backup_count_widget.setMaximumWidth(200)
        layout.addWidget(spreadsheet_backup_count_widget)
        layout.addSpacing(16)

        # ── Budget Groups ──
        if self.db and self.selected_profile:
            layout.addWidget(section_label("Budget Groups"))
            layout.addSpacing(4)

            self.budget_groups_list = QListWidget()
            self.budget_groups_list.setMaximumHeight(150)
            self.budget_groups_list.setStyleSheet("font-size: 13px; padding: 4px;")
            self.load_budget_groups()
            layout.addWidget(self.budget_groups_list)
            layout.addSpacing(4)

            add_group_row = QHBoxLayout()
            add_group_row.setSpacing(8)
            self.new_group_input = QLineEdit()
            self.new_group_input.setPlaceholderText("New group name...")
            self.new_group_input.setStyleSheet(input_style)
            self.new_group_input.setMinimumHeight(input_height)
            add_group_row.addWidget(self.new_group_input)

            add_group_button = QPushButton("Add Group")
            add_group_button.setStyleSheet(btn_style)
            add_group_button.setMinimumHeight(input_height)
            add_group_button.clicked.connect(self.add_budget_group)
            add_group_row.addWidget(add_group_button)

            delete_group_button = QPushButton("Delete Selected")
            delete_group_button.setStyleSheet("padding: 10px 20px; border: 1px solid #8B0000; border-radius: 5px; font-size: 13px; font-weight: bold; color: #ef5350;")
            delete_group_button.setMinimumHeight(input_height)
            delete_group_button.clicked.connect(self.delete_budget_group)
            add_group_row.addWidget(delete_group_button)

            layout.addLayout(add_group_row)
            layout.addSpacing(16)

        # ── AI Configuration ──
        if self.db:
            layout.addWidget(section_label("AI Budget Analysis"))
            hint = QLabel("Use any OpenAI-compatible server (Ollama, llama.cpp, LM Studio)")
            hint.setStyleSheet("font-size: 12px; color: #90a4ae;")
            layout.addWidget(hint)
            layout.addSpacing(4)

            self.ai_enabled_checkbox = QCheckBox("Enable AI Analysis")
            self.ai_enabled_checkbox.setStyleSheet("font-size: 13px;")
            current_enabled = self.db.get_setting("ai_enabled") == "true"
            self.ai_enabled_checkbox.setChecked(current_enabled)
            layout.addWidget(self.ai_enabled_checkbox)
            layout.addSpacing(8)

            layout.addWidget(field_label("AI Server URL"))
            self.ai_url_input = QLineEdit()
            self.ai_url_input.setPlaceholderText("http://localhost:11434/v1")
            current_url = self.db.get_setting("ai_server_url") or ""
            self.ai_url_input.setText(current_url)
            self.ai_url_input.setStyleSheet(input_style)
            self.ai_url_input.setMinimumHeight(input_height)
            layout.addWidget(self.ai_url_input)
            layout.addSpacing(8)

            layout.addWidget(field_label("Model"))
            self.ai_model_input = QLineEdit()
            current_model = self.db.get_setting("ai_model") or "qwen2.5:0.5b"
            self.ai_model_input.setText(current_model)
            self.ai_model_input.setStyleSheet(input_style)
            self.ai_model_input.setMinimumHeight(input_height)
            layout.addWidget(self.ai_model_input)
            layout.addSpacing(8)

            save_ai_button = QPushButton("Save AI Settings")
            save_ai_button.setStyleSheet(btn_style)
            save_ai_button.setMinimumHeight(input_height)
            save_ai_button.clicked.connect(self.save_ai_settings)
            layout.addWidget(save_ai_button)
            layout.addSpacing(16)

        # ── Server Connection ──
        layout.addWidget(section_label("Server Connection"))
        layout.addSpacing(4)

        server_hint = QLabel(
            "Leave blank to use local database. Set a server URL to sync with a remote Budgie server.\n"
            "Restart required after changing."
        )
        server_hint.setStyleSheet("font-size: 12px; color: #90a4ae;")
        server_hint.setWordWrap(True)
        layout.addWidget(server_hint)
        layout.addSpacing(4)

        layout.addWidget(field_label("Server URL"))
        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("http://192.168.1.4:8002")
        current_server_url = self._read_server_url()
        self.server_url_input.setText(current_server_url)
        self.server_url_input.setStyleSheet(input_style)
        self.server_url_input.setMinimumHeight(input_height)
        layout.addWidget(self.server_url_input)
        layout.addSpacing(4)

        server_btn_row = QHBoxLayout()
        server_btn_row.setSpacing(8)

        test_conn_button = QPushButton("Test Connection")
        test_conn_button.setStyleSheet(btn_style)
        test_conn_button.setMinimumHeight(input_height)
        test_conn_button.clicked.connect(self.test_server_connection)
        server_btn_row.addWidget(test_conn_button)

        save_server_button = QPushButton("Save")
        save_server_button.setStyleSheet(btn_style)
        save_server_button.setMinimumHeight(input_height)
        save_server_button.clicked.connect(self.save_server_url)
        server_btn_row.addWidget(save_server_button)

        clear_server_button = QPushButton("Clear")
        clear_server_button.setStyleSheet(
            "padding: 10px 20px; border: 1px solid #8B0000; border-radius: 5px; "
            "font-size: 13px; font-weight: bold; color: #ef5350;"
        )
        clear_server_button.setMinimumHeight(input_height)
        clear_server_button.clicked.connect(self.clear_server_url)
        server_btn_row.addWidget(clear_server_button)

        layout.addLayout(server_btn_row)
        layout.addSpacing(16)

        # ── Export / Import ──
        if self.db and self.selected_profile:
            layout.addWidget(section_label("Export / Import"))
            layout.addSpacing(4)

            export_import_hint = QLabel(
                "Export the current profile to a JSON file, or import a profile from a previously exported file."
            )
            export_import_hint.setStyleSheet("font-size: 12px; color: #90a4ae;")
            export_import_hint.setWordWrap(True)
            layout.addWidget(export_import_hint)
            layout.addSpacing(4)

            export_import_row = QHBoxLayout()
            export_import_row.setSpacing(8)

            export_button = QPushButton("Export Profile")
            export_button.setStyleSheet(btn_style)
            export_button.setMinimumHeight(input_height)
            export_button.clicked.connect(self.export_profile)
            export_import_row.addWidget(export_button)

            import_button = QPushButton("Import Profile")
            import_button.setStyleSheet(btn_style)
            import_button.setMinimumHeight(input_height)
            import_button.clicked.connect(self.import_profile)
            export_import_row.addWidget(import_button)

            layout.addLayout(export_import_row)
            layout.addSpacing(16)

        # ── Tutorial ──
        if self.db:
            layout.addWidget(section_label("Help"))
            layout.addSpacing(4)

            restart_tutorial_button = QPushButton("Restart Tutorial")
            restart_tutorial_button.setStyleSheet(btn_style)
            restart_tutorial_button.setMinimumHeight(input_height)
            restart_tutorial_button.clicked.connect(self.restart_tutorial)
            layout.addWidget(restart_tutorial_button)

        layout.addStretch(1)

        self.exec()

    def load_budget_groups(self):
        """Load budget groups into the list widget."""
        if not self.db or not self.selected_profile:
            return
        
        self.budget_groups_list.clear()
        budget_groups = self.db.fetch_budget_groups(self.selected_profile.id)
        for group in budget_groups:
            self.budget_groups_list.addItem(f"{group.name} (ID: {group.id})")
            # Store the group ID in the item data
            item = self.budget_groups_list.item(self.budget_groups_list.count() - 1)
            item.setData(1, group.id)  # Store group ID in user role
    
    def add_budget_group(self):
        """Add a new budget group."""
        group_name = self.new_group_input.text().strip()
        if not group_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a group name.")
            return
        
        try:
            self.db.create_budget_group(self.selected_profile.id, group_name)
            self.new_group_input.clear()
            self.load_budget_groups()
            QMessageBox.information(self, "Success", f"Budget group '{group_name}' has been created.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create budget group: {str(e)}")
    
    def delete_budget_group(self):
        """Delete the selected budget group."""
        current_item = self.budget_groups_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a budget group to delete.")
            return
        
        group_id = current_item.data(1)
        group_name = current_item.text().split(" (ID:")[0]
        
        reply = QMessageBox.question(
            self,
            "Delete Budget Group",
            f"Are you sure you want to delete budget group '{group_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_budget_group(group_id)
                self.load_budget_groups()
                QMessageBox.information(self, "Success", f"Budget group '{group_name}' has been deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete budget group: {str(e)}")

    def save_ai_settings(self):
        """Save AI configuration settings."""
        try:
            server_url = self.ai_url_input.text().strip()
            model = self.ai_model_input.text().strip() or "qwen2.5:0.5b"
            enabled = self.ai_enabled_checkbox.isChecked()

            self.db.set_setting("ai_server_url", server_url)
            self.db.set_setting("ai_model", model)
            self.db.set_setting("ai_enabled", str(enabled).lower())

            QMessageBox.information(self, "AI Settings", "AI settings have been saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save AI settings: {str(e)}")

    def on_theme_changed(self, index):
        """Handle theme change."""
        if not self.selected_profile:
            return
        
        new_theme = self.theme_combo.itemData(index)
        
        # Update theme in database using Database wrapper method
        self.db.update_profile_theme(self.selected_profile.id, new_theme)
        
        # Update the profile object in memory
        self.selected_profile.theme = new_theme
        
        # Apply theme immediately
        from ui.theme import get_theme, set_current_theme
        from PyQt6.QtWidgets import QApplication
        set_current_theme(new_theme)
        theme = get_theme(new_theme)
        QApplication.instance().setStyleSheet(theme.get_stylesheet())
        
        QMessageBox.information(
            self, "Theme Changed",
            f"Theme changed to {new_theme.title()}. The new theme has been applied."
        )
    
    def restart_tutorial(self):
        self.db.set_setting("onboarding_completed", "")
        OnboardingWizard(self.db, self).exec()

    # ── Server URL helpers ──

    @staticmethod
    def _server_url_config_path() -> str:
        config_dir = os.path.expanduser("~/.config/budgie")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "server_url")

    def _read_server_url(self) -> str:
        path = self._server_url_config_path()
        if os.path.isfile(path):
            try:
                return open(path, "r").read().strip()
            except OSError:
                pass
        return ""

    def test_server_connection(self):
        url = self.server_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "No URL", "Please enter a server URL first.")
            return
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{url.rstrip('/')}/profiles",
                method="GET",
                headers={"Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                import json as _json
                profiles = _json.loads(data)
                count = len(profiles) if isinstance(profiles, list) else 0
            QMessageBox.information(
                self,
                "Connection Successful",
                f"Connected to server. Found {count} profile(s).",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Could not reach the server:\n{e}",
            )

    def save_server_url(self):
        url = self.server_url_input.text().strip()
        try:
            path = self._server_url_config_path()
            with open(path, "w") as f:
                f.write(url)
            QMessageBox.information(
                self,
                "Server URL Saved",
                "Server URL saved. Please restart Budgie for the change to take effect.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save server URL: {e}")

    def clear_server_url(self):
        try:
            path = self._server_url_config_path()
            if os.path.isfile(path):
                os.remove(path)
            self.server_url_input.clear()
            QMessageBox.information(
                self,
                "Server URL Cleared",
                "Server URL cleared. Budgie will use the local database on next restart.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear server URL: {e}")

    # ── Export / Import ──

    def export_profile(self):
        """Export the current profile to a JSON file."""
        if not self.db or not self.selected_profile:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Profile",
            f"{self.selected_profile.name}_export.json",
            "JSON Files (*.json);;All Files (*)",
        )
        if not file_path:
            return

        try:
            export_data = self._build_export_data()
            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            QMessageBox.information(
                self,
                "Export Successful",
                f"Profile '{self.selected_profile.name}' exported to:\n{file_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export profile:\n{e}")

    def _build_export_data(self) -> dict:
        """Build export JSON either via API client or local Database."""
        from api.client import ApiClient

        if isinstance(self.db, ApiClient):
            return self.db.export_profile(self.selected_profile.id)

        # Local database export
        profile = self.selected_profile
        profile_id = profile.id

        accounts = self.db.fetch_accounts(profile_id)
        budget_groups = self.db.fetch_budget_groups(profile_id)
        budget_items = self.db.fetch_budget_items(profile_id)
        debts = self.db.fetch_debts(profile_id)
        extrapolation_items = self.db.fetch_extrapolation_items(profile_id)

        group_map = {g.id: g.name for g in budget_groups}
        budget_item_map = {bi.id: bi.name for bi in budget_items}
        debt_map = {d.id: d.name for d in debts}

        def date_to_iso(val):
            if val is None:
                return None
            if hasattr(val, "isoformat"):
                return val.isoformat()
            return str(val)

        exported_accounts = []
        for acc in accounts:
            ledger_entries = self.db.fetch_ledger_items(acc.id)
            exported_accounts.append({
                "name": acc.name,
                "account_type": acc.account_type,
                "ledger_entries": [
                    {
                        "name": le.name,
                        "paid_date": date_to_iso(le.paid_date),
                        "income_date": date_to_iso(le.income_date),
                        "type": le.type,
                        "amount": float(le.amount) if le.amount else 0.0,
                    }
                    for le in ledger_entries
                ],
            })

        exported_groups = [{"name": g.name} for g in budget_groups]

        exported_budget_items = []
        for bi in budget_items:
            periods = []
            if hasattr(bi, "periods") and bi.periods:
                periods = [
                    {"type": p.type, "value": p.value, "business_day": getattr(p, "business_day", None)}
                    for p in bi.periods
                ]
            exported_budget_items.append({
                "name": bi.name,
                "type": bi.type,
                "amount": float(bi.amount) if bi.amount else 0.0,
                "start_date": date_to_iso(bi.start_date),
                "end_date": date_to_iso(bi.end_date),
                "budget_group_name": group_map.get(bi.budget_group_id) or (bi.budget_group_id if isinstance(bi.budget_group_id, str) else None),
                "debt_name": debt_map.get(bi.debt_id) if hasattr(bi, "debt_id") and bi.debt_id else None,
                "periods": periods,
            })

        exported_debts = [
            {
                "name": d.name,
                "total_amount": float(d.total_amount),
                "remaining_amount": float(d.remaining_amount),
                "min_payment": float(d.min_payment),
                "interest_rate": float(d.interest_rate),
            }
            for d in debts
        ]

        exported_extrap = []
        for ei in extrapolation_items:
            exported_extrap.append({
                "due_date": date_to_iso(ei.due_date),
                "amount": float(ei.amount) if ei.amount else 0.0,
                "income_date": date_to_iso(ei.income_date),
                "budget_item_name": budget_item_map.get(ei.budget_item_id),
                "ledger_entry_linked": ei.ledger_entry_id is not None,
                "category": ei.category,
                "name": ei.name,
            })

        from datetime import datetime

        return {
            "version": 1,
            "exported_at": datetime.now().isoformat(),
            "profile": {
                "name": profile.name,
                "theme": profile.theme or "dark",
                "hidden_through": date_to_iso(profile.hidden_through),
            },
            "accounts": exported_accounts,
            "budget_groups": exported_groups,
            "budget_items": exported_budget_items,
            "debts": exported_debts,
            "extrapolation_items": exported_extrap,
        }

    def import_profile(self):
        """Import a profile from a JSON file."""
        if not self.db:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Profile",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                import_data = json.load(f)

            result = self._run_import(import_data)
            profile_name = result.get("profile_name", "Unknown")
            QMessageBox.information(
                self,
                "Import Successful",
                f"Profile '{profile_name}' imported successfully.\n"
                "Please restart or re-select profiles to see it.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Failed to import profile:\n{e}")

    def _run_import(self, import_data: dict) -> dict:
        """Run import either via API client or local Database."""
        from api.client import ApiClient

        if isinstance(self.db, ApiClient):
            return self.db.import_profile(import_data)

        # Local database import
        db = self.db
        profile_info = import_data.get("profile", {})

        # 1. Create the profile
        profile = db.create_profile(profile_info.get("name", "Imported Profile"))

        # 2. Update theme
        theme = profile_info.get("theme")
        if theme:
            db.update_profile_theme(profile.id, theme)

        # 3. Update hidden_through
        hidden_through = profile_info.get("hidden_through")
        if hidden_through:
            db.update_profile_hidden_through(profile.id, hidden_through)

        # 4. Create budget groups
        group_name_to_id = {}
        for g in import_data.get("budget_groups", []):
            new_group = db.create_budget_group(profile.id, g["name"])
            group_name_to_id[g["name"]] = new_group.id

        # 5. Create debts
        debt_name_to_id = {}
        for d in import_data.get("debts", []):
            new_debt = db.create_debt(
                profile.id,
                d["name"],
                d.get("total_amount", 0),
                d.get("remaining_amount", 0),
                d.get("min_payment", 0),
                d.get("interest_rate", 0),
            )
            debt_name_to_id[d["name"]] = new_debt.id

        # 6. Create accounts and ledger entries
        for acc in import_data.get("accounts", []):
            new_account = db.create_account(
                profile.id, acc["name"], acc.get("account_type", "Checking"), 0.0
            )
            for le in acc.get("ledger_entries", []):
                db.create_ledger_entry(
                    name=le["name"],
                    date=le["paid_date"],
                    incomeDate=le["income_date"],
                    type=le.get("type", "Expense"),
                    amount=le.get("amount", 0),
                    accountId=new_account.id,
                )

        # 7. Create budget items
        from database.budget_item_period import BudgetItemPeriod

        budget_item_name_to_id = {}
        for bi in import_data.get("budget_items", []):
            group_id = group_name_to_id.get(bi.get("budget_group_name"))
            debt_id = debt_name_to_id.get(bi.get("debt_name"))
            periods = [
                BudgetItemPeriod(
                    type=p["type"],
                    value=p["value"],
                    business_day=p.get("business_day"),
                    budget_item_id=None,
                )
                for p in bi.get("periods", [])
            ]
            new_item = db.create_budget_item(
                profileId=profile.id,
                name=bi["name"],
                type=bi.get("type", "Expense"),
                amount=bi.get("amount", 0),
                group=group_id,
                start_date=bi.get("start_date"),
                end_date=bi.get("end_date"),
                periods=periods,
                debt_id=debt_id,
            )
            budget_item_name_to_id[bi["name"]] = new_item.id

        # 8. Create extrapolation items
        for ei in import_data.get("extrapolation_items", []):
            budget_item_id = budget_item_name_to_id.get(ei.get("budget_item_name"))
            db.create_extrapolation_item(
                profileId=profile.id,
                date=ei["due_date"],
                amount=ei.get("amount", 0),
                income_date=ei.get("income_date"),
                budget_item_id=budget_item_id,
                category=ei.get("category"),
                name=ei.get("name"),
            )

        return {
            "success": True,
            "profile_id": profile.id,
            "profile_name": profile.name,
        }

    def open_location(self, folder_path):
        if platform.system() == "Windows":
            os.startfile(folder_path)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, folder_path])
        # os.startfile(spreadsheet_backup_location_widget.text())
