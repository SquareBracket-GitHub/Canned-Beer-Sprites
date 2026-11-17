import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QFileDialog,
    QFormLayout, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QPlainTextEdit, QSpinBox, QSplitter, QVBoxLayout, QWidget,
)
from .core import Sprite, layout, xml_text


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("canned beer sprites")
        self.resize(1200, 760)
        self.setAcceptDrops(True)
        self.images = {}
        self.atlas = None
        self.placements = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh)
        split = QSplitter()
        self.setCentralWidget(split)
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.addWidget(QLabel("Images"))
        buttons = QHBoxLayout()
        for title, action in [("Add files", self.add_files), ("Add folder", self.add_folder)]:
            button = QPushButton(title)
            button.clicked.connect(action)
            buttons.addWidget(button)
        lv.addLayout(buttons)
        self.items = QListWidget()
        self.items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.items.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.items.model().rowsMoved.connect(self.schedule)
        lv.addWidget(self.items)
        remove = QPushButton("Remove selected")
        remove.clicked.connect(self.remove_selected)
        lv.addWidget(remove)
        split.addWidget(left)
        center = QWidget()
        cv = QVBoxLayout(center)
        cv.addWidget(QLabel("Sheet Preview"))
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("#34383d"))
        empty_layout = QVBoxLayout(self.view.viewport())
        self.empty_hint = QLabel("Drop files or folders here")
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_hint.setStyleSheet("color: #b8bcc2; background: transparent;")
        self.empty_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        empty_layout.addWidget(self.empty_hint)
        cv.addWidget(self.view, 3)
        self.xml = QPlainTextEdit()
        self.xml.setReadOnly(True)
        cv.addWidget(self.xml, 1)
        split.addWidget(center)
        right = QWidget()
        form = QFormLayout(right)
        self.mode = QComboBox()
        self.mode.addItems(["Rows", "Uniform grid", "Compact"])
        form.addRow("Layout", self.mode)
        self.auto = QCheckBox("Automatic")
        self.auto.setChecked(True)
        form.addRow("Sheet size", self.auto)
        self.width = self.spin(1, 16384, 1024)
        self.height = self.spin(1, 16384, 1024)
        self.width.setEnabled(False)
        self.height.setEnabled(False)
        form.addRow("Width", self.with_unit(self.width))
        form.addRow("Height", self.with_unit(self.height))
        self.gap = self.spin(0, 256, 0)
        form.addRow("Spacing", self.with_unit(self.gap))
        self.name = QLineEdit("spritesheet")
        form.addRow("Output name", self.name)
        self.export_button = QPushButton("Generate")
        self.export_button.clicked.connect(self.export)
        form.addRow(self.export_button)
        self.warning = QLabel()
        self.warning.setWordWrap(True)
        self.warning.setStyleSheet("color: #e53935;")
        self.warning.hide()
        form.addRow(self.warning)
        split.addWidget(right)
        split.setSizes([250, 650, 300])
        self.mode.currentIndexChanged.connect(self.schedule)
        self.auto.toggled.connect(self.auto_changed)
        for spin in [self.width, self.height, self.gap]:
            spin.valueChanged.connect(self.schedule)
        self.name.textChanged.connect(self.schedule)
        self.refresh()

    @staticmethod
    def with_unit(spin):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(spin, 1)
        layout.addWidget(QLabel("px"))
        return row

    @staticmethod
    def spin(low, high, value):
        spin = QSpinBox()
        spin.setRange(low, high)
        spin.setValue(value)
        return spin

    def schedule(self, *_):
        self.timer.start(100)

    def auto_changed(self, checked):
        self.width.setEnabled(not checked)
        self.height.setEnabled(not checked)
        self.schedule()

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add images", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif *.tif *.tiff)")
        self.add_paths(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select image folder")
        if folder:
            self.add_paths([folder])

    def add_paths(self, paths):
        candidates = []
        for value in paths:
            path = Path(value)
            if path.is_dir():
                candidates.extend(sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif", ".tif", ".tiff"}))
            else:
                candidates.append(path)
        errors = []
        for path in candidates:
            key = str(path.resolve())
            if key in self.images:
                continue
            image = QImage(key)
            if image.isNull():
                errors.append(path.name)
                continue
            self.images[key] = image
            item = QListWidgetItem(f"{path.name}  ·  {image.width()} × {image.height()}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setToolTip(key)
            self.items.addItem(item)
        self.refresh()
        if errors:
            self.show_warning("Cannot read these files:\n" + "\n".join(errors[:20]))

    def remove_selected(self):
        for item in self.items.selectedItems():
            self.images.pop(item.data(Qt.ItemDataRole.UserRole))
            self.items.takeItem(self.items.row(item))
        self.refresh()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_paths([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()])
        event.acceptProposedAction()

    def output_name(self):
        name = self.name.text().strip()
        if not name or name in {".", ".."} or any(c in name for c in '<>:"/\\|?*') or name.endswith('.'):
            raise ValueError("Enter a valid output filename.")
        return name

    def refresh(self):
        self.timer.stop()
        self.atlas = None
        self.scene.clear()
        self.xml.clear()
        self.export_button.setEnabled(False)
        self.warning.clear()
        self.warning.hide()
        self.empty_hint.setVisible(self.items.count() == 0)
        if not self.items.count():
            return
        try:
            name = self.output_name()
            sprites = []
            for i in range(self.items.count()):
                key = self.items.item(i).data(Qt.ItemDataRole.UserRole)
                image = self.images[key]
                sprites.append(Sprite(Path(key), image.width(), image.height()))
            size = None if self.auto.isChecked() else (self.width.value(), self.height.value())
            w,h,placements = layout(sprites, ["rows", "grid", "compact"][self.mode.currentIndex()], self.gap.value(), size)
            atlas = QImage(w,h,QImage.Format.Format_ARGB32)
            if atlas.isNull():
                raise ValueError("Cannot allocate sheet memory. Reduce its size.")
            atlas.fill(Qt.GlobalColor.transparent)
            painter = QPainter(atlas)
            for p in placements:
                painter.drawImage(p.x,p.y,self.images[str(p.sprite.path)])
            painter.end()
            self.atlas = atlas
            self.placements = placements
            self.xml.setPlainText(xml_text(name+".png", placements))
            self.scene.addPixmap(QPixmap.fromImage(atlas))
            self.scene.setSceneRect(0,0,w,h)
            self.view.fitInView(self.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
            self.export_button.setEnabled(True)
        except ValueError as error:
            self.show_warning(str(error))

    def show_warning(self, message):
        self.warning.setText(message)
        self.warning.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "scene"):
            self.view.fitInView(self.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)

    def export(self):
        self.refresh()
        if self.atlas is None:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if not folder:
            return
        base = Path(folder) / self.output_name()
        png = base.with_name(base.name+".png")
        xml = base.with_name(base.name+".xml")
        if (png.exists() or xml.exists()) and QMessageBox.question(self, "Overwrite files", "Output files already exist. Overwrite them?") != QMessageBox.StandardButton.Yes:
            return
        try:
            if not self.atlas.save(str(png), "PNG"):
                raise OSError("Failed to save PNG.")
            xml.write_text(self.xml.toPlainText(), encoding="utf-8")
            QMessageBox.information(self, "canned beer sprites", "well seamed!")
        except OSError as error:
            self.show_warning(f"Save failed: {error}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("canned beer sprites")
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
