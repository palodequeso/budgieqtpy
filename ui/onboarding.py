from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


ONBOARDING_STEPS = [
    (
        "Welcome to Budgie",
        "Budgie helps you plan your finances by scheduling bills and income "
        "onto a calendar. Here's how to get started.",
    ),
    (
        "Create a Profile",
        "Profiles keep budgets separate — one for yourself, one shared with "
        "a partner, etc. You can create more anytime from Settings.",
    ),
    (
        "Add Your Accounts",
        "Head to the Accounts tab and add your bank accounts (checking, "
        "savings, credit cards). These track where your money flows.",
    ),
    (
        "Set Up Your Budget",
        "In the Budget tab, add your recurring income and expenses. Each "
        "item has a schedule — 'monthly on the 1st', 'biweekly on Friday', etc.",
    ),
    (
        "Run Extrapolation",
        "Go to the Calendar tab and click Extrapolate. This projects your "
        "budget items into the future so you can see what's coming.",
    ),
    (
        "You're Ready!",
        "The calendar is your main workspace. Mark items as paid, add "
        "one-off expenses, compute savings, and hide past pay periods as you go.",
    ),
]


HELP_TEXTS = {
    "accounts": "Add your bank accounts here. Each account tracks its own ledger of transactions.",
    "budget": "Define recurring income and expenses with schedules. These get projected onto your calendar.",
    "debts": "Track debts and interest rates. Budgie can compute optimal payment plans from your surplus.",
    "reconcile": "Import bank CSV statements and match transactions against your budget to find discrepancies.",
    "extrapolate": "Projects your budget items onto the calendar. Run this after adding or changing budget items.",
    "got_paid": "Record a paycheck arrival. Marks the income as received and creates a ledger entry.",
    "unscheduled": "Items that couldn't fit into a pay period. Assign them to a column manually.",
    "one_off": "Add a non-recurring expense or income to a specific pay period.",
    "savings": "Compute leftover amounts per pay period and schedule transfers to savings.",
    "hide_column": "Hide past pay periods you're done managing to keep the view clean.",
}


class HelpIcon(QPushButton):
    def __init__(self, help_text: str, parent=None):
        super().__init__("?", parent)
        self._help_text = help_text
        self.setFixedSize(22, 22)
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #546e7a;
                border-radius: 11px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }
        """)
        self.setToolTip(help_text)
        self.clicked.connect(self._show_help)

    def _show_help(self):
        QMessageBox.information(self, "Help", self._help_text)


class OnboardingWizard(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_step = 0
        self.setWindowTitle("Welcome to Budgie")
        self.setMinimumWidth(520)
        self.setMinimumHeight(320)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(30, 24, 30, 20)

        # Step indicator dots
        self.dots_layout = QHBoxLayout()
        self.dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dots_layout.setSpacing(8)
        self.dot_labels = []
        for i in range(len(ONBOARDING_STEPS)):
            dot = QLabel()
            dot.setFixedSize(10, 10)
            self.dot_labels.append(dot)
            self.dots_layout.addWidget(dot)
        layout.addLayout(self.dots_layout)

        # Stacked widget for pages
        self.stack = QStackedWidget()
        for title, body in ONBOARDING_STEPS:
            page = QWidget()
            page_layout = QVBoxLayout()
            page_layout.setSpacing(12)

            title_label = QLabel(title)
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_layout.addWidget(title_label)

            body_label = QLabel(body)
            body_label.setWordWrap(True)
            body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            body_label.setStyleSheet("font-size: 13px; line-height: 1.6; padding: 10px 20px;")
            page_layout.addWidget(body_label)

            page_layout.addStretch(1)
            page.setLayout(page_layout)
            self.stack.addWidget(page)

        layout.addWidget(self.stack)

        # Navigation buttons
        button_layout = QHBoxLayout()

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self._go_back)
        button_layout.addWidget(self.back_button)

        button_layout.addStretch(1)

        self.skip_button = QPushButton("Skip")
        self.skip_button.setStyleSheet("color: #546e7a;")
        self.skip_button.clicked.connect(self._finish)
        button_layout.addWidget(self.skip_button)

        self.next_button = QPushButton("Next")
        self.next_button.setStyleSheet("font-weight: bold;")
        self.next_button.clicked.connect(self._go_next)
        button_layout.addWidget(self.next_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self._update_ui()

    def _update_ui(self):
        self.stack.setCurrentIndex(self.current_step)
        self.back_button.setVisible(self.current_step > 0)

        is_last = self.current_step == len(ONBOARDING_STEPS) - 1
        self.next_button.setText("Get Started" if is_last else "Next")

        for i, dot in enumerate(self.dot_labels):
            if i == self.current_step:
                dot.setStyleSheet("background-color: palette(highlight); border-radius: 5px;")
            else:
                dot.setStyleSheet("background-color: #546e7a; border-radius: 5px;")

    def _go_next(self):
        if self.current_step < len(ONBOARDING_STEPS) - 1:
            self.current_step += 1
            self._update_ui()
        else:
            self._finish()

    def _go_back(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._update_ui()

    def _finish(self):
        if self.db:
            self.db.set_setting("onboarding_completed", "true")
        self.accept()
