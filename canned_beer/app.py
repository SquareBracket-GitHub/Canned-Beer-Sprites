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
        self.setWindowTitle("canned beer")
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
        lv.addWidget(QLabel("이미지"))
        buttons = QHBoxLayout()
        for title, action in [("파일 추가", self.add_files), ("폴더 추가", self.add_folder)]:
            button = QPushButton(title)
            button.clicked.connect(action)
            buttons.addWidget(button)
        lv.addLayout(buttons)
        self.items = QListWidget()
        self.items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.items.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.items.model().rowsMoved.connect(self.schedule)
        lv.addWidget(self.items)
        remove = QPushButton("선택 삭제")
        remove.clicked.connect(self.remove_selected)
        lv.addWidget(remove)
        split.addWidget(left)
        center = QWidget()
        cv = QVBoxLayout(center)
        cv.addWidget(QLabel("시트 미리보기 · 파일 또는 폴더를 창에 놓으세요"))
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("#34383d"))
        cv.addWidget(self.view, 3)
        self.xml = QPlainTextEdit()
        self.xml.setReadOnly(True)
        cv.addWidget(self.xml, 1)
        split.addWidget(center)
        right = QWidget()
        form = QFormLayout(right)
        self.mode = QComboBox()
        self.mode.addItems(["가로 순서대로", "동일 크기 격자", "빈 공간 최소화"])
        form.addRow("배치", self.mode)
        self.auto = QCheckBox("자동 결정")
        self.auto.setChecked(True)
        form.addRow("시트 크기", self.auto)
        self.width = self.spin(1, 16384, 1024)
        self.height = self.spin(1, 16384, 1024)
        self.width.setEnabled(False)
        self.height.setEnabled(False)
        form.addRow("가로 px", self.width)
        form.addRow("세로 px", self.height)
        self.gap = self.spin(0, 256, 0)
        form.addRow("간격 px", self.gap)
        self.name = QLineEdit("spritesheet")
        form.addRow("출력 이름", self.name)
        self.export_button = QPushButton("PNG + XML 내보내기")
        self.export_button.clicked.connect(self.export)
        form.addRow(self.export_button)
        hint = QLabel("원본 크기와 투명도 유지\n회전·자르기 없음\n한 장을 초과하면 크기 변경 안내")
        hint.setWordWrap(True)
        form.addRow(hint)
        split.addWidget(right)
        split.setSizes([250, 650, 300])
        self.mode.currentIndexChanged.connect(self.schedule)
        self.auto.toggled.connect(self.auto_changed)
        for spin in [self.width, self.height, self.gap]:
            spin.valueChanged.connect(self.schedule)
        self.name.textChanged.connect(self.schedule)
        self.refresh()

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
        files, _ = QFileDialog.getOpenFileNames(self, "이미지 추가", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif *.tif *.tiff)")
        self.add_paths(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "이미지 폴더 선택")
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
            QMessageBox.warning(self, "읽기 실패", "다음 파일을 읽을 수 없습니다:\n" + "\n".join(errors[:20]))

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
            raise ValueError("출력 이름에 유효한 파일명을 입력해주세요.")
        return name

    def refresh(self):
        self.timer.stop()
        self.atlas = None
        self.scene.clear()
        self.xml.clear()
        self.export_button.setEnabled(False)
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
                raise ValueError("시트 메모리를 확보하지 못했습니다. 크기를 줄여주세요.")
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
            self.statusBar().showMessage(f"{len(sprites)}개 이미지 · {w} × {h}px")
            self.export_button.setEnabled(True)
        except ValueError as error:
            self.statusBar().showMessage(str(error))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "scene"):
            self.view.fitInView(self.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)

    def export(self):
        self.refresh()
        if self.atlas is None:
            return
        folder = QFileDialog.getExistingDirectory(self, "PNG와 XML을 저장할 폴더")
        if not folder:
            return
        base = Path(folder) / self.output_name()
        png = base.with_name(base.name+".png")
        xml = base.with_name(base.name+".xml")
        if (png.exists() or xml.exists()) and QMessageBox.question(self, "덮어쓰기", "같은 이름의 출력 파일이 있습니다. 덮어쓸까요?") != QMessageBox.StandardButton.Yes:
            return
        try:
            if not self.atlas.save(str(png), "PNG"):
                raise OSError("PNG 저장에 실패했습니다.")
            xml.write_text(self.xml.toPlainText(), encoding="utf-8")
            self.statusBar().showMessage(f"저장 완료: {png.name}, {xml.name}")
        except OSError as error:
            QMessageBox.warning(self,"저장 실패",str(error))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("canned beer")
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
