import os
import platform
import subprocess
import sys
from PyQt6.QtWidgets import QVBoxLayout, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton


class Settings(QDialog):
    layout: QVBoxLayout = None

    def __init__(self):
        super().__init__()
        self.render_settings()

    def render_settings(self):
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()
        self.setLayout(layout)

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

        layout.addStretch(1)

        self.exec()

    def open_location(self, folder_path):
        if platform.system() == "Windows":
            os.startfile(folder_path)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, folder_path])
        # os.startfile(spreadsheet_backup_location_widget.text())
