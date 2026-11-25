import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QFileDialog,
    QFormLayout, QGraphicsScene, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QPlainTextEdit, QSpinBox, QSplitter, QVBoxLayout, QWidget,
)
from canned_beer.core import Sprite, layout, xml_text
from canned_beer.theme import apply_theme
from canned_beer.widgets import ImageDelegate, PreviewView, XmlHighlighter


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("canned beer sprites")
        self.resize(1280, 820)
        self.setMinimumSize(1100, 680)
        self.setAcceptDrops(True)
        self.images = {}
        self.atlas = None
        self.placements = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh)
        split = QSplitter()
        split.setHandleWidth(6)
        split.setChildrenCollapsible(False)
        self.setCentralWidget(split)
        left = QWidget()
        left.setObjectName("imagesPanel")
        left.setMinimumWidth(240)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(16, 18, 16, 16)
        lv.setSpacing(12)
        lv.addWidget(self.heading("Images"))
        buttons = QHBoxLayout()
        for title, action in [("Add files", self.add_files), ("Add folder", self.add_folder)]:
            button = QPushButton(title)
            button.clicked.connect(action)
            buttons.addWidget(button)
        lv.addLayout(buttons)
        self.items = QListWidget()
        self.items.setItemDelegate(ImageDelegate(self.items))
        self.items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.items.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.items.model().rowsMoved.connect(self.schedule)
        list_empty_layout = QVBoxLayout(self.items.viewport())
        self.list_hint = QLabel("No images yet\nAdd files or a folder to begin.")
        self.list_hint.setObjectName("secondaryLabel")
        self.list_hint.setWordWrap(True)
        self.list_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        list_empty_layout.addWidget(self.list_hint)
        lv.addWidget(self.items)
        remove = QPushButton("Remove selected")
        remove.clicked.connect(self.remove_selected)
        lv.addWidget(remove)
        split.addWidget(left)
        center = QWidget()
        center.setObjectName("workspacePanel")
        center.setMinimumWidth(470)
        cv = QVBoxLayout(center)
        cv.setContentsMargins(16, 18, 16, 16)
        cv.setSpacing(12)
        cv.addWidget(self.heading("Sheet Preview"))
        preview_controls = QHBoxLayout()
        preview_controls.setSpacing(8)
        background_label = QLabel("Background")
        background_label.setObjectName("secondaryLabel")
        preview_controls.addWidget(background_label)
        self.preview_background = QComboBox()
        self.preview_background.addItems(["Checkerboard", "Dark Slate", "Light Slate"])
        self.preview_background.setAccessibleName("Preview background")
        self.preview_background.setToolTip("Preview only; never included in the exported PNG.")
        preview_controls.addWidget(self.preview_background, 1)
        self.checker_label = QLabel("Tile")
        self.checker_label.setObjectName("secondaryLabel")
        preview_controls.addWidget(self.checker_label)
        self.checker_size = QComboBox()
        self.checker_size.addItems(["8 px", "16 px", "32 px"])
        self.checker_size.setCurrentIndex(1)
        self.checker_size.setAccessibleName("Checkerboard tile size")
        preview_controls.addWidget(self.checker_size)
        cv.addLayout(preview_controls)
        self.scene = QGraphicsScene(self)
        self.view = PreviewView(self.scene)
        empty_layout = QVBoxLayout(self.view.viewport())
        self.empty_hint = QLabel("Drop files or folders here")
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_hint.setStyleSheet("color: #E1E8F0; background: #192536; padding: 10px; border-radius: 0px;")
        self.empty_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        empty_layout.addStretch()
        empty_layout.addWidget(self.empty_hint, 0, Qt.AlignmentFlag.AlignCenter)
        empty_layout.addStretch()
        cv.addWidget(self.view, 3)
        xml_header = QHBoxLayout()
        xml_header.addWidget(self.heading("XML Output"))
        xml_header.addStretch()
        self.copy_xml = QPushButton("Copy XML")
        self.copy_xml.setToolTip("Copy the generated XML to the clipboard")
        self.copy_xml.clicked.connect(self.copy_xml_output)
        xml_header.addWidget(self.copy_xml)
        cv.addLayout(xml_header)
        self.xml = QPlainTextEdit()
        self.xml.setReadOnly(True)
        self.xml.setPlaceholderText("Generated XML will appear here.")
        self.xml_highlighter = XmlHighlighter(self.xml.document())
        self.xml.textChanged.connect(lambda: self.copy_xml.setEnabled(bool(self.xml.toPlainText())))
        self.copy_xml.setEnabled(False)
        cv.addWidget(self.xml, 1)
        self.preview_background.currentTextChanged.connect(self.update_preview_background)
        self.checker_size.currentIndexChanged.connect(self.update_preview_background)
        split.addWidget(center)
        right = QWidget()
        right.setObjectName("settingsPanel")
        right.setMinimumWidth(300)
        settings = QVBoxLayout(right)
        settings.setContentsMargins(18, 18, 18, 16)
        settings.setSpacing(18)
        settings.addWidget(self.heading("Settings"))

        def group(title):
            box = QGroupBox(title)
            form = QFormLayout(box)
            form.setContentsMargins(0, 16, 0, 4)
            form.setHorizontalSpacing(12)
            form.setVerticalSpacing(12)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            settings.addWidget(box)
            return form

        layout_form = group("Layout")
        self.mode = QComboBox()
        self.mode.addItems(["Rows", "Uniform grid", "Compact"])
        layout_form.addRow("Packing", self.mode)
        canvas_form = group("Canvas")
        self.auto = QCheckBox("Automatic")
        self.auto.setChecked(True)
        canvas_form.addRow("Size", self.auto)
        self.width = self.spin(1, 16384, 1024)
        self.height = self.spin(1, 16384, 1024)
        self.width.setEnabled(False)
        self.height.setEnabled(False)
        canvas_form.addRow("Width", self.with_unit(self.width))
        canvas_form.addRow("Height", self.with_unit(self.height))
        self.gap = self.spin(0, 256, 0)
        canvas_form.addRow("Spacing", self.with_unit(self.gap))
        output_form = group("Output")
        self.name = QLineEdit("spritesheet")
        output_form.addRow("Name", self.name)
        self.export_button = QPushButton("Generate")
        self.export_button.setObjectName("generateButton")
        self.export_button.clicked.connect(self.export)
        settings.addWidget(self.export_button)
        self.warning = QLabel()
        self.warning.setWordWrap(True)
        self.warning.setObjectName("warningLabel")
        self.warning.hide()
        settings.addWidget(self.warning)
        settings.addStretch()
        for box in right.findChildren(QGroupBox):
            form = box.layout()
            for row in range(form.rowCount()):
                label = form.itemAt(row, QFormLayout.ItemRole.LabelRole)
                if label:
                    label.widget().setFixedWidth(58)
        split.addWidget(right)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setStretchFactor(2, 0)
        split.setSizes([260, 700, 310])
        self.mode.currentIndexChanged.connect(self.schedule)
        self.auto.toggled.connect(self.auto_changed)
        for spin in [self.width, self.height, self.gap]:
            spin.valueChanged.connect(self.schedule)
        self.name.textChanged.connect(self.schedule)
        self.refresh()

    @staticmethod
    def heading(text):
        label = QLabel(text)
        label.setObjectName("sectionHeading")
        return label

    def update_preview_background(self, *_):
        mode = self.preview_background.currentText()
        checker = mode == "Checkerboard"
        self.checker_size.setEnabled(checker)
        self.checker_label.setEnabled(checker)
        self.view.set_background(mode, (8, 16, 32)[self.checker_size.currentIndex()])

    def copy_xml_output(self):
        QApplication.clipboard().setText(self.xml.toPlainText())

    @staticmethod
    def with_unit(spin):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(spin, 1)
        unit = QLabel("px")
        unit.setObjectName("secondaryLabel")
        unit.setFixedWidth(18)
        layout.addWidget(unit)
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
            item.setData(Qt.ItemDataRole.UserRole + 1, path.name)
            item.setData(Qt.ItemDataRole.UserRole + 2, f"{image.width()} × {image.height()} px")
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
        self.list_hint.setVisible(self.items.count() == 0)
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
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "SquareBracket.CannedBeerSprites")
    app = QApplication(sys.argv)
    app.setApplicationName("canned beer sprites")
    apply_theme(app)
    icon = QIcon(str(Path(__file__).resolve().parent / "resources" / "cbs.png"))
    if icon.isNull():
        raise RuntimeError("Application icon is missing or unreadable.")
    app.setWindowIcon(icon)
    window = Window()
    window.show()
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(1000, app.quit)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
