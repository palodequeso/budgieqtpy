import sys
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication

from ui import MainWindow
from ui.theme import get_theme, set_current_theme
from database.database import Database


if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

def main():
    app = QApplication(sys.argv)
    
    # Try to load theme from last selected profile
    db = Database()
    default_theme = "dark"
    
    last_profile_id = db.get_last_profile_id()
    if last_profile_id:
        last_profile = db.get_profile_by_id(last_profile_id)
        if last_profile and last_profile.theme:
            default_theme = last_profile.theme
    
    # Apply theme on startup
    set_current_theme(default_theme)
    theme = get_theme(default_theme)
    app.setStyleSheet(theme.get_stylesheet())
    
    window = MainWindow()
    window.resize(1920, 1080)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
