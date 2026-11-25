"""UI regressions: preview decoration must never become exported pixels."""
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
from PySide6.QtCore import Qt

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication
from canned_beer.app import Window
from canned_beer.core import Sprite, layout, xml_text
from canned_beer.theme import COLORS, apply_theme


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        apply_theme(cls.app)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.window = Window()
        self.window.show()
        self.app.processEvents()
        self.addCleanup(self.window.close)
        image = QImage(6, 8, QImage.Format.Format_ARGB32)
        image.fill(QColor(0, 0, 0, 0))
        image.setPixelColor(2, 3, QColor(200, 100, 80, 128))
        image.setPixelColor(3, 4, QColor(40, 120, 160, 255))
        self.source = self.root / 'sprite.png'
        self.assertTrue(image.save(str(self.source)))

    def test_background_rendering_and_screen_pixel_tile_size(self):
        view = self.window.view
        for zoom in (0.5, 3):
            view.resetTransform()
            view.scale(zoom, zoom)
            image = view.viewport().grab().toImage()
            self.assertEqual(image.pixelColor(2, 2).name().lower(), COLORS['checker_light'].lower())
            self.assertEqual(image.pixelColor(18, 2).name().lower(), COLORS['checker_dark'].lower())
        for mode, token in (('Dark Slate', 'dark_slate'), ('Light Slate', 'light_slate')):
            self.window.preview_background.setCurrentText(mode)
            image = view.viewport().grab().toImage()
            self.assertEqual(image.pixelColor(2, 2).name().lower(), COLORS[token].lower())

    def test_startup_when_entry_point_is_outside_package(self):
        # Nuitka places the entry point at the bundle root, away from package data.
        script = (
            "import sys; import canned_beer.app as app; "
            "app.__file__ = 'app.py'; "
            "sys.argv = ['app.py', '--smoke-test']; app.main()"
        )
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
        env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1])
        result = subprocess.run([sys.executable, '-c', script], cwd=self.root,
                                env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_preview_modes_do_not_change_exported_png_or_xml(self):
        window = self.window
        window.add_paths([str(self.source)])
        window.auto.setChecked(False)
        window.width.setValue(64)
        window.height.setValue(64)
        for mode_index, mode in enumerate(('rows', 'grid', 'compact')):
            window.mode.setCurrentIndex(mode_index)
            _, _, placements = layout([Sprite(self.source, 6, 8)], mode, 0, (64, 64))
            expected_xml = xml_text('spritesheet.png', placements)
            reference = None
            for bg in ('Checkerboard', 'Dark Slate', 'Light Slate'):
                window.preview_background.setCurrentText(bg)
                window.view.viewport().grab()  # Exercise background painting before export.
                output = self.root / f'{mode}-{bg}'
                output.mkdir()
                with patch('canned_beer.app.QFileDialog.getExistingDirectory', return_value=str(output)), \
                     patch('canned_beer.app.QMessageBox.information'):
                    window.export()
                result = QImage(str(output / 'spritesheet.png'))
                self.assertEqual(result.pixelColor(63, 63).alpha(), 0)
                self.assertEqual(result.pixelColor(2, 3), QColor(200, 100, 80, 128))
                self.assertEqual(result.pixelColor(3, 4), QColor(40, 120, 160, 255))
                if reference is None:
                    reference = result
                self.assertEqual(result, reference)
                self.assertEqual((output / 'spritesheet.xml').read_text(encoding='utf-8'), expected_xml)

    def test_copy_xml_and_invalid_output_states(self):
        window = self.window
        self.assertFalse(window.copy_xml.isEnabled())
        window.add_paths([str(self.source)])
        self.assertTrue(window.copy_xml.isEnabled())
        window.copy_xml.click()
        self.assertEqual(self.app.clipboard().text(), window.xml.toPlainText())
        window.name.setText('invalid/name')
        window.refresh()
        self.assertFalse(window.copy_xml.isEnabled())
        self.assertFalse(window.export_button.isEnabled())
        self.assertFalse(window.warning.isHidden())

    def test_folder_import_duplicate_paths_reorder_and_remove(self):
        window = self.window
        nested = self.root / 'nested'
        nested.mkdir()
        other = nested / 'other.png'
        other.write_bytes(self.source.read_bytes())
        window.add_paths([str(self.root), str(self.source)])
        self.assertEqual(window.items.count(), 2)
        moved = window.items.takeItem(1)
        window.items.insertItem(0, moved)
        window.refresh()
        key = moved.data(Qt.ItemDataRole.UserRole)
        self.assertEqual(window.placements[0].sprite.path, Path(key))
        moved.setSelected(True)
        window.remove_selected()
        self.assertEqual(window.items.count(), 1)
        self.assertNotIn(key, window.images)


if __name__ == '__main__':
    unittest.main()
