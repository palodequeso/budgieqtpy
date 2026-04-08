from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
    QScrollArea,
)
from PyQt6.QtCore import pyqtSignal as Signal, Qt
from PyQt6.QtGui import QFont, QPalette, QColor
from api.profile import ProfileAPI
from database.profile import Profile


class Profiles(QWidget):
    profile_selected = Signal(Profile)

    profiles: list[Profile] = None

    def __init__(self, db, profiles):
        super().__init__()
        self.profilesApi = ProfileAPI(db)
        self.profiles = profiles
        self.render_profiles()

    def render_profiles(self):
        self.profiles = self.profilesApi.get_profiles()

        # Clear existing layout if any
        old_layout = self.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)

        # Main vertical layout with padding
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # Welcome section
        welcome_container = QWidget()
        welcome_container.setStyleSheet("border-radius: 10px; padding: 30px;")
        welcome_layout = QVBoxLayout()
        
        # App title
        title = QLabel("Budgie")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Your Personal Budget Calendar")
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("margin-top: 10px;")
        welcome_layout.addWidget(subtitle)
        
        # Description
        description = QLabel(
            "Budgie helps you plan and track your budget over time.\n"
            "Schedule recurring expenses, track income, and see your financial future."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("margin-top: 15px; line-height: 1.6;")
        welcome_layout.addWidget(description)
        
        welcome_container.setLayout(welcome_layout)
        main_layout.addWidget(welcome_container)
        
        # Profiles section
        if self.profiles:
            profiles_label = QLabel("Select Your Profile")
            profiles_label_font = QFont()
            profiles_label_font.setPointSize(18)
            profiles_label_font.setBold(True)
            profiles_label.setFont(profiles_label_font)
            profiles_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(profiles_label)
            
            # Profiles grid
            profiles_container = QWidget()
            profiles_layout = QHBoxLayout()
            profiles_layout.setSpacing(20)
            profiles_layout.addStretch(1)
            
            for profile in self.profiles:
                profile_card = QPushButton(profile.name)
                profile_card.setMinimumWidth(180)
                profile_card.setMinimumHeight(120)
                profile_card.setStyleSheet("""
                    QPushButton {
                        border: 2px solid;
                        border-radius: 10px;
                        color: white;
                        font-size: 16px;
                        font-weight: bold;
                        padding: 20px;
                    }
                    QPushButton:hover {
                        background-color: #455a64;
                        border-color: #1976d2;
                    }
                    QPushButton:pressed {
                        background-color: #1976d2;
                    }
                """)
                profile_card.clicked.connect(
                    lambda checked=False, p=profile: self.profile_selected.emit(p)
                )
                profiles_layout.addWidget(profile_card)
            
            profiles_layout.addStretch(1)
            profiles_container.setLayout(profiles_layout)
            main_layout.addWidget(profiles_container)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("margin: 20px 0;")
        main_layout.addWidget(divider)
        
        # Create profile section
        create_label = QLabel("Create New Profile")
        create_label_font = QFont()
        create_label_font.setPointSize(16)
        create_label_font.setBold(True)
        create_label.setFont(create_label_font)
        create_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(create_label)
        
        # Create profile form
        create_container = QWidget()
        create_layout = QHBoxLayout()
        create_layout.addStretch(1)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter profile name...")
        name_input.setMinimumWidth(250)
        name_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #1976d2;
            }
        """)
        create_layout.addWidget(name_input)
        
        create_button = QPushButton("Create Profile")
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px 25px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        create_button.clicked.connect(lambda: self.create_profile(name_input.text()))
        name_input.returnPressed.connect(lambda: self.create_profile(name_input.text()))
        create_layout.addWidget(create_button)
        
        create_layout.addStretch(1)
        create_container.setLayout(create_layout)
        main_layout.addWidget(create_container)
        
        main_layout.addStretch(1)
        
        self.setLayout(main_layout)
        self.show()

    def create_profile(self, name):
        if not name.strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Input", "Please enter a profile name.")
            return
        try:
            self.profilesApi.create_profile(name)
            self.render_profiles()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to create profile: {str(e)}")
