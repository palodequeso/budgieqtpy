"""
Centralized theme management for the Qt application.

By default, the app uses the system/KDE theme (Breeze, etc.).
The stylesheet is kept minimal — only app-specific overrides that
don't conflict with the desktop environment's look and feel.
"""


class Theme:
    """Base theme class."""

    # Status colors (used directly by app code, not overridden by system)
    success: str = "#27ae60"
    error: str = "#e74c3c"
    warning: str = "#f39c12"
    info: str = "#3498db"

    @classmethod
    def get_stylesheet(cls) -> str:
        """Return minimal stylesheet — let the system theme handle the rest.

        The QPushButton rule ensures buttons keep a visible border when
        inline stylesheets override properties like border-radius or
        padding, which causes KDE/Breeze to drop native button styling.
        """
        return """
            QPushButton {
                border: 1px solid #546e7a;
            }
        """


class DarkTheme(Theme):
    """Marker for dark mode — inherits system dark theme."""
    pass


class LightTheme(Theme):
    """Marker for light mode — inherits system light theme."""
    pass


def get_theme(theme_name: str = "dark") -> Theme:
    """Get theme by name."""
    if theme_name == "light":
        return LightTheme
    return DarkTheme


# Global current theme tracker
_current_theme = "dark"

def set_current_theme(theme_name: str):
    """Set the current active theme."""
    global _current_theme
    _current_theme = theme_name

def get_current_theme() -> Theme:
    """Get the currently active theme class."""
    return get_theme(_current_theme)
