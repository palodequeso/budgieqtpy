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
)
from database.database import Database
from database.profile import Profile


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
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Theme Selection (if profile is provided)
        if self.db and self.selected_profile:
            theme_row = QHBoxLayout()
            theme_label = QLabel("Theme:")
            theme_label.setStyleSheet("font-weight: bold;")
            theme_row.addWidget(theme_label)
            
            self.theme_combo = QComboBox()
            self.theme_combo.addItem("Dark", "dark")
            self.theme_combo.addItem("Light", "light")
            
            # Set current theme
            current_theme = self.selected_profile.theme if self.selected_profile.theme else "dark"
            index = 0 if current_theme == "dark" else 1
            self.theme_combo.setCurrentIndex(index)
            
            self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
            theme_row.addWidget(self.theme_combo)
            theme_row.addStretch(1)
            layout.addLayout(theme_row)
            
            layout.addWidget(QLabel(""))  # Spacer

        spreadsheet_backup_location_row = QHBoxLayout()
        spreadsheet_backup_location_row.addWidget(QLabel("Spreadsheet Backup Location:"))
        spreadsheet_backup_location_widget = QLineEdit('./schedule-spreadsheets/')
        spreadsheet_backup_location_row.addWidget(spreadsheet_backup_location_widget)
        open_location_button = QPushButton("Open Location")
        open_location_button.clicked.connect(
            lambda: self.open_location(spreadsheet_backup_location_widget.text())
        )
        spreadsheet_backup_location_row.addWidget(open_location_button)
        # spreadsheet_backup_location_row.addStretch(1)
        layout.addLayout(spreadsheet_backup_location_row)

        spreadsheet_backup_count_row = QHBoxLayout()
        spreadsheet_backup_count_row.addWidget(QLabel("Spreadsheet Backup Count:"))
        spreadsheet_backup_count_widget = QLineEdit('5000')
        spreadsheet_backup_count_row.addWidget(spreadsheet_backup_count_widget)
        spreadsheet_backup_count_row.addStretch(1)
        layout.addLayout(spreadsheet_backup_count_row)

        # Budget Groups Management Section (if profile is provided)
        if self.db and self.selected_profile:
            layout.addWidget(QLabel(""))  # Spacer
            budget_groups_label = QLabel("Budget Groups Management:")
            budget_groups_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(budget_groups_label)
            
            # List of budget groups
            self.budget_groups_list = QListWidget()
            self.budget_groups_list.setMaximumHeight(150)
            self.load_budget_groups()
            layout.addWidget(self.budget_groups_list)
            
            # Add new budget group
            add_group_row = QHBoxLayout()
            add_group_row.addWidget(QLabel("New Budget Group:"))
            self.new_group_input = QLineEdit()
            self.new_group_input.setPlaceholderText("Enter group name")
            add_group_row.addWidget(self.new_group_input)
            
            add_group_button = QPushButton("Add Group")
            add_group_button.clicked.connect(self.add_budget_group)
            add_group_row.addWidget(add_group_button)
            
            delete_group_button = QPushButton("Delete Selected")
            delete_group_button.setStyleSheet("background-color: #8B0000; color: white;")
            delete_group_button.clicked.connect(self.delete_budget_group)
            add_group_row.addWidget(delete_group_button)
            
            layout.addLayout(add_group_row)

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
    
    def open_location(self, folder_path):
        if platform.system() == "Windows":
            os.startfile(folder_path)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, folder_path])
        # os.startfile(spreadsheet_backup_location_widget.text())
