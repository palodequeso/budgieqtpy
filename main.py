import sys
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication

from ui import MainWindow


if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1920, 1080)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
