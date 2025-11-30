"""
Centralized theme management for the Qt application.
Provides light and dark color schemes with consistent styling.
"""

class Theme:
    """Base theme class with color definitions."""
    
    # Background colors
    bg_primary: str = None
    bg_secondary: str = None
    bg_tertiary: str = None
    bg_hover: str = None
    
    # Text colors
    text_primary: str = None
    text_secondary: str = None
    text_muted: str = None
    
    # UI element colors
    border: str = None
    button_bg: str = None
    button_text: str = None
    button_hover: str = None
    
    # Status colors
    success: str = "#27ae60"
    error: str = "#e74c3c"
    warning: str = "#f39c12"
    info: str = "#3498db"
    
    @classmethod
    def get_stylesheet(cls) -> str:
        """Generate QApplication stylesheet from theme colors."""
        return f"""
            QMainWindow, QDialog, QWidget {{
                background-color: {cls.bg_primary};
                color: {cls.text_primary};
            }}
            
            QLabel {{
                color: {cls.text_primary};
            }}
            
            QPushButton {{
                background-color: {cls.button_bg};
                color: {cls.button_text};
                border: 1px solid {cls.border};
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {cls.button_hover};
            }}
            
            QPushButton:pressed {{
                background-color: {cls.bg_secondary};
            }}
            
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {{
                background-color: {cls.bg_secondary};
                color: {cls.text_primary};
                border: 1px solid {cls.border};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 1px solid {cls.info};
            }}
            
            QTableWidget {{
                background-color: {cls.bg_primary};
                color: {cls.text_primary};
                gridline-color: {cls.border};
                border: 1px solid {cls.border};
            }}
            
            QTableWidget::item {{
                padding: 4px;
            }}
            
            QTableWidget::item:selected {{
                background-color: {cls.bg_hover};
            }}
            
            QHeaderView::section {{
                background-color: {cls.bg_secondary};
                color: {cls.text_primary};
                padding: 6px;
                border: 1px solid {cls.border};
                font-weight: bold;
            }}
            
            QListWidget {{
                background-color: {cls.bg_secondary};
                color: {cls.text_primary};
                border: 1px solid {cls.border};
                border-radius: 4px;
            }}
            
            QListWidget::item:selected {{
                background-color: {cls.bg_hover};
            }}
            
            QScrollBar:vertical {{
                background-color: {cls.bg_secondary};
                width: 12px;
                border: none;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {cls.border};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {cls.text_muted};
            }}
            
            QScrollBar:horizontal {{
                background-color: {cls.bg_secondary};
                height: 12px;
                border: none;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {cls.border};
                border-radius: 6px;
                min-width: 20px;
            }}
            
            QScrollBar::add-line, QScrollBar::sub-line {{
                border: none;
                background: none;
            }}
            
            QMenuBar {{
                background-color: {cls.bg_secondary};
                color: {cls.text_primary};
            }}
            
            QMenuBar::item:selected {{
                background-color: {cls.bg_hover};
            }}
            
            QMenu {{
                background-color: {cls.bg_secondary};
                color: {cls.text_primary};
                border: 1px solid {cls.border};
            }}
            
            QMenu::item:selected {{
                background-color: {cls.bg_hover};
            }}
            
            QCheckBox {{
                color: {cls.text_primary};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {cls.border};
                background-color: {cls.bg_primary};
            }}
            
            QTabBar::tab {{
                background-color: {cls.bg_secondary};
                color: {cls.text_primary};
                padding: 8px 16px;
                border: 1px solid {cls.border};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {cls.bg_primary};
                font-weight: bold;
            }}
            
            QTabBar::tab:hover {{
                background-color: {cls.bg_hover};
            }}
            
            QMessageBox {{
                background-color: {cls.bg_primary};
            }}
        """


class DarkTheme(Theme):
    """Dark theme color scheme."""
    
    bg_primary = "#1e272e"
    bg_secondary = "#2c3e50"
    bg_tertiary = "#34495e"
    bg_hover = "#3d5a80"
    
    text_primary = "#ecf0f1"
    text_secondary = "#bdc3c7"
    text_muted = "#7f8c8d"
    
    border = "#4a5f7f"
    button_bg = "#34495e"
    button_text = "#ecf0f1"
    button_hover = "#415a77"


class LightTheme(Theme):
    """Light theme color scheme."""
    
    bg_primary = "#ffffff"
    bg_secondary = "#f5f5f5"
    bg_tertiary = "#e0e0e0"
    bg_hover = "#e8e8e8"
    
    text_primary = "#212121"
    text_secondary = "#424242"
    text_muted = "#757575"
    
    border = "#d0d0d0"
    button_bg = "#e0e0e0"
    button_text = "#212121"
    button_hover = "#d0d0d0"


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
