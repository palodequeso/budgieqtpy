from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget

from database import Database
from database.profile import Profile
from ui.accounts import Accounts
from ui.budget import Budget
from ui.calendar import Calendar
from ui.profiles import Profiles
from ui.settings import Settings


class MainWindow(QMainWindow):
    selected_profile: Profile = None
    profiles: list[Profile] = []
    db = Database()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Budgie")
        layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.profiles = self.db.fetch_profiles()
        self.render_menu()
        self.render_profiles()

    def render_menu(self):
        menu = self.menuBar()
        fileMenu = menu.addMenu("File")
        profilesMenu = fileMenu.addMenu("Profiles")
        for profile in self.profiles:
            profileAction = profilesMenu.addAction(profile.name)
            profileAction.triggered.connect(
                lambda profile_selected, p=profile: self.profile_selected(p)
            )

        settingsAction = fileMenu.addAction("Settings")
        settingsAction.triggered.connect(self.open_settings)
        exitAction = fileMenu.addAction("Exit")
        exitAction.triggered.connect(self.close)

    def open_settings(self):
        settings = Settings()

    def render_profiles(self):
        profile_chooser = Profiles(self.db, self.profiles)
        profile_chooser.profile_selected.connect(self.profile_selected)
        self.setCentralWidget(profile_chooser)

    def profile_selected(self, profile):
        self.selected_profile = profile
        self.render_profile()

    def render_calendar(self, tabWidget):
        calendar_widget = Calendar(self.db, self.selected_profile)
        tabWidget.addTab(calendar_widget, "Calendar")

    def render_accounts(self, tabWidget):
        accounts_widget = Accounts(self.db, self.selected_profile)
        tabWidget.addTab(accounts_widget, "Accounts")

    def render_budget(self, tabWidget):
        budget_widget = Budget(self.db, self.selected_profile)
        tabWidget.addTab(budget_widget, "Budget")

    def render_profile(self):
        tabWidget = QTabWidget()
        self.render_calendar(tabWidget)
        self.render_accounts(tabWidget)
        self.render_budget(tabWidget)
        self.setCentralWidget(tabWidget)
