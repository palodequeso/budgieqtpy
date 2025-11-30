from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QApplication

from api.profile import ProfileAPI
from database.database import Database
from database.profile import Profile
from ui.accounts import Accounts
from ui.budget import Budget
from ui.calendar import Calendar
from ui.profiles import Profiles
from ui.settings import Settings
from ui.theme import get_theme, set_current_theme


class MainWindow(QMainWindow):
    db = Database() # Factor this connection into a singleton that the apis can reference directly?
    profileApi = ProfileAPI(db)
    selected_profile: Profile = None
    profiles: list[Profile] = []

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Budgie")
        layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.profiles = self.profileApi.get_profiles()
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
        settings = Settings(self.db, self.selected_profile)

    def render_profiles(self):
        profile_chooser = Profiles(self.db, self.profiles)
        profile_chooser.profile_selected.connect(self.profile_selected)
        self.setCentralWidget(profile_chooser)

    def profile_selected(self, profile):
        self.selected_profile = profile
        # Save this as the last selected profile
        self.db.set_last_profile_id(profile.id)
        self.apply_theme()
        self.render_profile()
    
    def apply_theme(self):
        """Apply theme based on selected profile."""
        if self.selected_profile:
            theme_name = self.selected_profile.theme if self.selected_profile.theme else "dark"
            set_current_theme(theme_name)
            theme = get_theme(theme_name)
            QApplication.instance().setStyleSheet(theme.get_stylesheet())

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
