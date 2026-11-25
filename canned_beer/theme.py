"""Shared navy and indigo colors for widgets and Qt dialogs."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette


def apply_theme(app):
    app.setStyle("Fusion")
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    palette = QPalette()
    colors = {
        QPalette.ColorRole.Window: "#11182c",
        QPalette.ColorRole.WindowText: "#e8edff",
        QPalette.ColorRole.Base: "#0b1120",
        QPalette.ColorRole.AlternateBase: "#18223b",
        QPalette.ColorRole.Text: "#e8edff",
        QPalette.ColorRole.Button: "#253454",
        QPalette.ColorRole.ButtonText: "#e8edff",
        QPalette.ColorRole.Highlight: "#545dcc",
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: "#263454",
        QPalette.ColorRole.ToolTipText: "#e8edff",
        QPalette.ColorRole.Link: "#a5b4fc",
        QPalette.ColorRole.PlaceholderText: "#9aa9c9",
        QPalette.ColorRole.Light: "#405179",
        QPalette.ColorRole.Midlight: "#30405f",
        QPalette.ColorRole.Mid: "#263454",
        QPalette.ColorRole.Dark: "#080e1b",
        QPalette.ColorRole.Shadow: "#080e1b",
    }
    for role, color in colors.items():
        palette.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text,
                 QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor("#7887a8"))
    app.setPalette(palette)
    resources = (Path(__file__).resolve().parent / "resources").as_posix()
    app.setStyleSheet("""
        QWidget { font-size: 13px; }
        QLabel { background: transparent; }
        QLabel#sectionHeading { color: #b9c6ed; font-weight: 600; }
        QListWidget, QPlainTextEdit, QGraphicsView {
            background: #0b1120; border: 1px solid #2b395b;
            border-radius: 8px; selection-background-color: #424e9f;
            selection-color: #ffffff;
        }
        QListWidget { padding: 5px; }
        QListWidget::item { padding: 8px 6px; border-radius: 4px; }
        QListWidget::item:hover { background: #202d4c; }
        QListWidget::item:selected { background: #424e9f; color: #ffffff; }
        QPlainTextEdit { padding: 8px; font-family: Consolas, monospace; }
        QLineEdit, QSpinBox, QComboBox {
            background: #18223b; color: #e8edff;
            border: 1px solid #354568; border-radius: 5px;
            padding: 6px; min-height: 20px;
            selection-background-color: #545dcc;
        }
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #9aa5ff; }
        QLineEdit:disabled, QSpinBox:disabled {
            background: #141c30; color: #7887a8; border-color: #263454;
        }
        QComboBox QAbstractItemView {
            background: #18223b; color: #e8edff;
            selection-background-color: #424e9f; outline: none;
        }
        QSpinBox { padding-right: 22px; }
        QSpinBox::up-button, QSpinBox::down-button {
            width: 20px; background: #253454; border: none;
        }
        QSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; }
        QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #405179; }
        QSpinBox::up-button:disabled, QSpinBox::down-button:disabled { background: #141c30; }
        QSpinBox::up-arrow { image: url("@RESOURCES@/chevron-up.svg"); width: 10px; height: 6px; }
        QSpinBox::down-arrow { image: url("@RESOURCES@/chevron-down.svg"); width: 10px; height: 6px; }
        QComboBox { padding-right: 24px; }
        QComboBox::drop-down { width: 22px; border: none; }
        QComboBox::down-arrow { image: url("@RESOURCES@/chevron-down.svg"); width: 10px; height: 6px; }
        QPushButton {
            background: #253454; color: #e8edff;
            border: 1px solid #405179; border-radius: 6px;
            padding: 8px 10px; min-height: 18px;
        }
        QPushButton:hover { background: #304268; border-color: #7888bd; }
        QPushButton:pressed { background: #1b2844; }
        QPushButton:focus { border-color: #a5b4fc; }
        QPushButton#generateButton {
            background: #545dcc; border-color: #7d86ee;
            color: #ffffff; font-weight: 600;
        }
        QPushButton#generateButton:hover { background: #636de0; }
        QPushButton#generateButton:pressed { background: #454eae; }
        QPushButton:disabled, QPushButton#generateButton:disabled {
            background: #202b46; border-color: #2b395b; color: #7887a8;
        }
        QCheckBox { spacing: 8px; padding: 4px 0; }
        QCheckBox:focus { color: #c7d2fe; }
        QSplitter::handle { background: #11182c; }
        QSplitter::handle:hover { background: #405179; }
        QScrollBar:vertical { background: #11182c; width: 12px; }
        QScrollBar:horizontal { background: #11182c; height: 12px; }
        QScrollBar::handle { background: #405179; border-radius: 4px; }
        QScrollBar::handle:vertical { min-height: 24px; }
        QScrollBar::handle:horizontal { min-width: 24px; }
        QScrollBar::handle:hover { background: #6475a5; }
        QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
        QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
        QToolTip { background: #263454; color: #e8edff; border: 1px solid #53658f; }
    """.replace("@RESOURCES@", resources))
