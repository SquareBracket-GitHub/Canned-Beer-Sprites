"""Presentation-only preview, image-list, and XML helpers."""
from PySide6.QtCore import QRegularExpression, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPixmap, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import QGraphicsView, QStyle, QStyledItemDelegate, QStyleOptionViewItem

from canned_beer.theme import COLORS


class PreviewView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.background_mode = "Checkerboard"
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    def set_background(self, mode):
        self.background_mode = mode
        self.viewport().update()

    def drawBackground(self, painter, rect):
        # Paint in viewport pixels, independent of sprite zoom and export data.
        painter.save()
        painter.resetTransform()
        if self.background_mode == "Checkerboard":
            size = 16
            tile = QPixmap(size * 2, size * 2)
            tile.fill(QColor(COLORS['checker_dark']))
            tile_painter = QPainter(tile)
            color = QColor(COLORS['checker_light'])
            tile_painter.fillRect(0, 0, size, size, color)
            tile_painter.fillRect(size, size, size, size, color)
            tile_painter.end()
            painter.fillRect(self.viewport().rect(), QBrush(tile))
        else:
            token = 'light_slate' if self.background_mode == 'Light Slate' else 'dark_slate'
            painter.fillRect(self.viewport().rect(), QColor(COLORS[token]))
        painter.restore()


class ImageDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(180, 56)

    def paint(self, painter, option, index):
        styled = QStyleOptionViewItem(option)
        self.initStyleOption(styled, index)
        styled.text = ""
        style = styled.widget.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, styled, painter, styled.widget)
        painter.save()
        rect = option.rect.adjusted(10, 5, -10, -5)
        painter.setFont(option.font)
        painter.setPen(QColor(COLORS['text']))
        name = index.data(Qt.ItemDataRole.UserRole + 1) or index.data()
        name = option.fontMetrics.elidedText(name, Qt.TextElideMode.ElideMiddle, rect.width())
        painter.drawText(rect.adjusted(0, 0, 0, -21), Qt.AlignmentFlag.AlignVCenter, name)
        font = QFont(option.font)
        font.setPointSizeF(max(8, font.pointSizeF() - 1))
        painter.setFont(font)
        painter.setPen(QColor(COLORS['muted']))
        painter.drawText(rect.adjusted(0, 24, 0, 0), Qt.AlignmentFlag.AlignVCenter,
                         index.data(Qt.ItemDataRole.UserRole + 2) or "")
        painter.restore()


class XmlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        for expression, color in (
            (r'</?[\w:.-]+|/?>|<\?xml|\?>', COLORS['accent']),
            (r'[\w:.-]+(?=\s*=)', '#B5C5D5'),
            (r'"[^"]*"|\x27[^\x27]*\x27', '#A6BEAF'),
        ):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            self.rules.append((QRegularExpression(expression), fmt))

    def highlightBlock(self, text):
        for expression, fmt in self.rules:
            matches = expression.globalMatch(text)
            while matches.hasNext():
                match = matches.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
