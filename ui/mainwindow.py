import os

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QApplication

from api.profile import ProfileAPI
from database.database import Database
from database.profile import Profile
from ui.accounts import Accounts
from ui.budget import Budget
from ui.calendar import Calendar
from ui.dashboard import Dashboard
from ui.debts import Debts
from ui.profiles import Profiles
from ui.reconcile import Reconcile
from ui.settings import Settings
from ui.onboarding import OnboardingWizard
from ui.theme import get_theme, set_current_theme


class MainWindow(QMainWindow):
    selected_profile: Profile = None
    profiles: list[Profile] = []

    @staticmethod
    def _get_server_url() -> str | None:
        """Read server URL from config file, if set."""
        config_path = os.path.expanduser("~/.config/budgie/server_url")
        if os.path.isfile(config_path):
            try:
                url = open(config_path, "r").read().strip()
                if url:
                    return url
            except OSError:
                pass
        return None

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Budgie")

        # Choose backend: remote API or local database
        server_url = self._get_server_url()
        if server_url:
            from api.client import ApiClient
            self.db = ApiClient(server_url)
        else:
            self.db = Database()

        self.profileApi = ProfileAPI(self.db)

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
        if self.db.get_setting("onboarding_completed") != "true":
            OnboardingWizard(self.db, self).exec()
    
    def apply_theme(self):
        """Apply theme based on selected profile."""
        if self.selected_profile:
            theme_name = self.selected_profile.theme if self.selected_profile.theme else "dark"
            set_current_theme(theme_name)
            theme = get_theme(theme_name)
            QApplication.instance().setStyleSheet(theme.get_stylesheet())

    def render_dashboard(self, tabWidget):
        dashboard_widget = Dashboard(self.db, self.selected_profile)
        tabWidget.addTab(dashboard_widget, "Dashboard")

    def render_calendar(self, tabWidget):
        calendar_widget = Calendar(self.db, self.selected_profile)
        tabWidget.addTab(calendar_widget, "Calendar")

    def rebuild_calendar(self, tabWidget):
        """Replace the calendar tab with a fresh one (e.g., after debt payments saved)."""
        # Calendar is always the second tab (index 1), after Dashboard
        old = tabWidget.widget(1)
        tabWidget.removeTab(1)
        old.deleteLater()
        new_calendar = Calendar(self.db, self.selected_profile)
        tabWidget.insertTab(1, new_calendar, "Calendar")

    def render_accounts(self, tabWidget):
        accounts_widget = Accounts(self.db, self.selected_profile)
        tabWidget.addTab(accounts_widget, "Accounts")

    def render_budget(self, tabWidget):
        budget_widget = Budget(self.db, self.selected_profile)
        tabWidget.addTab(budget_widget, "Budget")

    def render_debts(self, tabWidget):
        debts_widget = Debts(self.db, self.selected_profile)
        debts_widget.payments_saved.connect(lambda: self.rebuild_calendar(tabWidget))
        tabWidget.addTab(debts_widget, "Debts")

    def render_reconcile(self, tabWidget):
        reconcile_widget = Reconcile(self.db, self.selected_profile)
        tabWidget.addTab(reconcile_widget, "Reconcile")

    def render_profile(self):
        tabWidget = QTabWidget()
        self.render_dashboard(tabWidget)
        self.render_calendar(tabWidget)
        self.render_accounts(tabWidget)
        self.render_budget(tabWidget)
        self.render_debts(tabWidget)
        self.render_reconcile(tabWidget)
        self.setCentralWidget(tabWidget)
