"""
BNSW Utils - Themes
----------------
This module provides theme management for the BNSW application.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class ThemeManager:
    """Theme manager for the BNSW application."""
    
    def __init__(self):
        """Initialize theme manager."""
        self.themes = {
            "Light": self._get_light_theme(),
            "Dark": self._get_dark_theme()
        }
    
    def apply_theme(self, window, theme_name):
        """
        Apply theme to window.
        
        Args:
            window: Window to apply theme to
            theme_name: Theme name
        """
        # Get theme
        theme = self.themes.get(theme_name)
        if not theme:
            return
        
        # Apply palette
        QApplication.setPalette(theme)
        
        # Apply stylesheet
        if theme_name == "Light":
            window.setStyleSheet(self._get_light_stylesheet())
        else:
            window.setStyleSheet(self._get_dark_stylesheet())
    
    def _get_light_theme(self):
        """
        Get light theme palette.
        
        Returns:
            QPalette: Light theme palette
        """
        palette = QPalette()
        
        # Set colors
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        return palette
    
    def _get_dark_theme(self):
        """
        Get dark theme palette.
        
        Returns:
            QPalette: Dark theme palette
        """
        palette = QPalette()
        
        # Set colors
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        return palette
    
    def _get_light_stylesheet(self):
        """
        Get light theme stylesheet.
        
        Returns:
            str: Light theme stylesheet
        """
        return """
        QMainWindow {
            background-color: #f0f0f0;
        }
        
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #e0e0e0;
            border: 1px solid #c0c0c0;
            padding: 6px 12px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom-color: #ffffff;
        }
        
        QTableWidget {
            gridline-color: #d0d0d0;
            selection-background-color: #e0e0e0;
            selection-color: #000000;
        }
        
        QTableWidget::item:selected {
            background-color: #e0e0e0;
        }
        
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 4px;
            border: 1px solid #c0c0c0;
        }
        
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #c0c0c0;
            padding: 6px 12px;
        }
        
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
        
        QLineEdit, QComboBox {
            background-color: #ffffff;
            border: 1px solid #c0c0c0;
            padding: 4px;
        }
        
        QProgressBar {
            border: 1px solid #c0c0c0;
            background-color: #ffffff;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #2a82da;
        }
        
        QStatusBar {
            background-color: #f0f0f0;
            border-top: 1px solid #c0c0c0;
        }
        """
    
    def _get_dark_stylesheet(self):
        """
        Get dark theme stylesheet.
        
        Returns:
            str: Dark theme stylesheet
        """
        return """
        QMainWindow {
            background-color: #353535;
        }
        
        QTabWidget::pane {
            border: 1px solid #202020;
            background-color: #252525;
        }
        
        QTabBar::tab {
            background-color: #353535;
            border: 1px solid #202020;
            padding: 6px 12px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #252525;
            border-bottom-color: #252525;
        }
        
        QTableWidget {
            gridline-color: #404040;
            selection-background-color: #404040;
            selection-color: #ffffff;
        }
        
        QTableWidget::item:selected {
            background-color: #404040;
        }
        
        QHeaderView::section {
            background-color: #353535;
            padding: 4px;
            border: 1px solid #202020;
        }
        
        QPushButton {
            background-color: #353535;
            border: 1px solid #202020;
            padding: 6px 12px;
        }
        
        QPushButton:hover {
            background-color: #404040;
        }
        
        QPushButton:pressed {
            background-color: #505050;
        }
        
        QLineEdit, QComboBox {
            background-color: #252525;
            border: 1px solid #202020;
            padding: 4px;
        }
        
        QProgressBar {
            border: 1px solid #202020;
            background-color: #252525;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #2a82da;
        }
        
        QStatusBar {
            background-color: #353535;
            border-top: 1px solid #202020;
        }
        """

# Create theme manager instance
_theme_manager = ThemeManager()

def set_light_theme(app):
    """
    Set light theme for application.
    
    Args:
        app: QApplication instance
    """
    # Create light palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(0, 0, 255))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    # Apply palette
    app.setPalette(palette)
    
    # Apply stylesheet
    app.setStyleSheet(_theme_manager._get_light_stylesheet())

def set_dark_theme(app):
    """
    Set dark theme for application.
    
    Args:
        app: QApplication instance
    """
    # Create dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    # Apply palette
    app.setPalette(palette)
    
    # Apply stylesheet
    app.setStyleSheet(_theme_manager._get_dark_stylesheet())
