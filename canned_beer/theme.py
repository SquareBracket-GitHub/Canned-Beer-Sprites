"""Frosted Navy / Winter Slate design tokens and shared widget styles."""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette

RESOURCE_DIR = Path(__file__).resolve().parent / 'resources'

COLORS = {
    'background': '#111927', 'left': '#151F2E', 'center': '#192536',
    'xml': '#101827', 'control': '#202D40', 'border': '#34445A',
    'text': '#E1E8F0', 'muted': '#9AAABD', 'accent': '#8EADC9',
    'selected': '#3D556D', 'hover': '#2C3D53', 'disabled': '#6F8197',
    'checker_light': '#42546A', 'checker_dark': '#34445A',
    'dark_slate': '#253345', 'light_slate': '#B8C4D0',
}


def apply_theme(app):
    app.setStyle('Fusion')
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    palette = QPalette()
    for role, token in {
        'Window': 'background', 'WindowText': 'text', 'Base': 'xml',
        'AlternateBase': 'center', 'Text': 'text', 'Button': 'control',
        'ButtonText': 'text', 'Highlight': 'selected', 'HighlightedText': 'text',
        'ToolTipBase': 'control', 'ToolTipText': 'text', 'Link': 'accent',
        'PlaceholderText': 'muted', 'Light': 'border', 'Midlight': 'hover',
        'Mid': 'border', 'Dark': 'xml', 'Shadow': 'xml',
    }.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(COLORS[token]))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text,
                 QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(COLORS['disabled']))
    app.setPalette(palette)
    styles = """
        QWidget { font-size: 13px; }
        QMainWindow { background: @background@; }
        QWidget#imagesPanel { background: @left@; }
        QWidget#workspacePanel { background: @center@; }
        QWidget#settingsPanel { background: @left@; }
        QLabel { background: transparent; }
        QLabel#sectionHeading { color: @text@; font-weight: 600; font-size: 14px; }
        QLabel#secondaryLabel { color: @muted@; }
        QLabel#warningLabel { color: #D9A6AA; }
        QGroupBox {
            border: none; border-top: 1px solid @border@;
            margin-top: 12px; padding-top: 6px; font-weight: 600;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 0; color: @accent@; }
        QListWidget, QPlainTextEdit, QGraphicsView {
            border: 1px solid @border@; border-radius: 0px;
            selection-background-color: @selected@; selection-color: @text@;
        }
        QListWidget { background: @left@; padding: 4px; }
        QListWidget::item { border-radius: 0px; }
        QListWidget::item:hover { background: @hover@; }
        QListWidget::item:selected { background: @selected@; }
        QPlainTextEdit { background: @xml@; padding: 10px; font-family: Consolas, monospace; }
        QLineEdit, QSpinBox, QComboBox {
            background: @control@; color: @text@;
            border: 1px solid @border@; border-radius: 0px;
            padding: 6px; min-height: 20px;
            selection-background-color: @selected@;
        }
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: @accent@; }
        QLineEdit:disabled, QSpinBox:disabled {
            background: @center@; color: @disabled@;
        }
        QComboBox QAbstractItemView {
            background: @control@; color: @text@;
            selection-background-color: @selected@; outline: none;
        }
        QSpinBox { padding-right: 22px; }
        QSpinBox::up-button, QSpinBox::down-button { width: 20px; background: @control@; border: none; }
        QSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; }
        QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: @hover@; }
        QSpinBox::up-button:disabled, QSpinBox::down-button:disabled { background: @center@; }
        QSpinBox::up-arrow { image: url("@RESOURCES@/chevron-up.svg"); width: 10px; height: 6px; }
        QSpinBox::down-arrow { image: url("@RESOURCES@/chevron-down.svg"); width: 10px; height: 6px; }
        QComboBox { padding-right: 24px; }
        QComboBox::drop-down { width: 22px; border: none; }
        QComboBox::down-arrow { image: url("@RESOURCES@/chevron-down.svg"); width: 10px; height: 6px; }
        QPushButton {
            background: @control@; color: @text@; border: 1px solid @border@;
            border-radius: 0px; padding: 8px 10px; min-height: 18px;
        }
        QPushButton:hover { background: @hover@; border-color: @muted@; }
        QPushButton:pressed { background: @selected@; }
        QPushButton:focus { border-color: @accent@; }
        QPushButton#generateButton {
            background: @accent@; border-color: @accent@;
            color: @background@; font-weight: 600;
        }
        QPushButton#generateButton:hover { background: #A1BCD3; }
        QPushButton#generateButton:pressed { background: #7B9BB7; }
        QPushButton:disabled, QPushButton#generateButton:disabled {
            background: @center@; border-color: @border@; color: @disabled@;
        }
        QCheckBox { spacing: 8px; padding: 4px 0; }
        QCheckBox:focus { color: @accent@; }
        QSplitter::handle { background: @background@; }
        QSplitter::handle:hover { background: @border@; }
        QScrollBar:vertical { background: @left@; width: 12px; }
        QScrollBar:horizontal { background: @left@; height: 12px; }
        QScrollBar::handle { background: @border@; border-radius: 0px; }
        QScrollBar::handle:vertical { min-height: 24px; }
        QScrollBar::handle:horizontal { min-width: 24px; }
        QScrollBar::handle:hover { background: @muted@; }
        QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
        QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
        QToolTip { background: @control@; color: @text@; border: 1px solid @border@; }
    """
    for token, color in COLORS.items():
        styles = styles.replace(f'@{token}@', color)
    resources = RESOURCE_DIR.as_posix()
    app.setStyleSheet(styles.replace('@RESOURCES@', resources))
