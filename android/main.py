"""PySide6 Android entry point with Python-QML bridge for Phase 2.

Proves the Python-QML communication channel works before building real app features.
The Bridge class exposes @Slot methods that QML can call directly, with results
displayed in the QML UI.

IMPORTANT: This must use QGuiApplication (not QApplication) and
QQmlApplicationEngine — QWidgets are not available on Android.
"""
import sys

from PySide6.QtCore import QObject, QUrl, Signal, Slot, Property
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


class Bridge(QObject):
    """Python-QML bridge proving slot communication works on Android."""

    resultChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result = ""

    @Slot(result=str)
    def ping(self):
        """Called from QML button tap. Returns a confirmation string."""
        msg = "Bridge OK — Python answered from @Slot"
        self._result = msg
        self.resultChanged.emit(msg)
        return msg

    def get_result(self):
        return self._result

    result = Property(str, get_result, notify=resultChanged)


def main():
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    bridge = Bridge()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl("qrc:/android/main.qml"))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
