from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import pyqtSignal as Signal
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
        verticalLayout = QVBoxLayout()

        for profile in self.profiles:
            hl = QHBoxLayout()
            hl.addStretch(1)
            profileButton = QPushButton(profile.name)
            profileButton.setFixedWidth(200)
            profileButton.setFixedHeight(200)
            profileButton.clicked.connect(
                lambda button_clicked, p=profile: self.profile_selected.emit(p)
            )
            hl.addWidget(profileButton)
            hl.addStretch(1)
            verticalLayout.addLayout(hl)
        verticalLayout.addStretch(1)

        horizontalLayout = QHBoxLayout()
        label = QLabel("New Profile")
        lineEdit = QLineEdit()
        button = QPushButton("Create")
        button.clicked.connect(lambda: self.create_profile(lineEdit.text()))
        horizontalLayout.addStretch(1)
        horizontalLayout.addWidget(label)
        horizontalLayout.addWidget(lineEdit)
        horizontalLayout.addWidget(button)
        verticalLayout.addLayout(horizontalLayout)

        self.setLayout(verticalLayout)
        self.show()

    def create_profile(self, name):
        self.profilesApi.create_profile(name)
        self.render_profiles()
