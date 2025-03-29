from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

class ThemeManager:
    @staticmethod
    def apply_dark_theme(app):
        palette = app.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
        palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(224, 224, 224))
        palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        app.setPalette(palette)

        # Additional widget-specific styling
        app.setStyleSheet("""
            QFrame {
                border: 1px solid #3F3F46;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                min-width: 80px;
                padding: 6px;
                font-weight: bold;
            }
            QTableWidget {
                gridline-color: #3F3F46;
            }
            QHeaderView::section {
                background-color: #333337;
                padding: 5px;
                border: 1px solid #3F3F46;
            }
            QProgressBar {
                border: 1px solid #3F3F46;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078D7;
            }
        """)

    @staticmethod
    def apply_light_theme(app):
        palette = app.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        app.setPalette(palette)

        # Additional widget-specific styling
        app.setStyleSheet("""
            QFrame {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                min-width: 80px;
                padding: 6px;
                font-weight: bold;
            }
            QTableWidget {
                gridline-color: #CCCCCC;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                padding: 5px;
                border: 1px solid #CCCCCC;
            }
            QProgressBar {
                border: 1px solid #CCCCCC;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078D7;
            }
        """)