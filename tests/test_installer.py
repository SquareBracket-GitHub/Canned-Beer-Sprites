import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.build_installer import build_installer


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exe = self.root / 'portable app.exe'
        self.exe.write_bytes(b'app')

    def test_required_signature_never_silently_builds_unsigned(self):
        with patch('scripts.build_installer.sys.platform', 'win32'):
            with self.assertRaisesRegex(ValueError, 'refusing an unsigned build'):
                build_installer(self.exe, '1.1.0', self.root, require_signature=True)

    def test_signs_and_verifies_app_and_installer(self):
        installer = self.root / 'canned-beer-sprites-v1.1.0-windows-x64-setup.exe'
        installer.write_bytes(b'installer')
        thumbprint = 'a' * 40
        with patch('scripts.build_installer.sys.platform', 'win32'), \
             patch('scripts.build_installer.find_compiler', return_value=Path('Inno Setup/ISCC.exe')), \
             patch('scripts.build_installer.find_signtool', return_value=Path('Windows SDK/signtool.exe')), \
             patch('scripts.build_installer.subprocess.run') as run:
            build_installer(self.exe, '1.1.0', self.root, thumbprint, True)
        calls = [call.args[0] for call in run.call_args_list]
        self.assertEqual(calls[0][1], 'sign')
        self.assertIn(str(self.exe.resolve()), calls[0])
        self.assertIn('/tr', calls[0])
        self.assertEqual(calls[1][1:4], ['verify', '/pa', '/all'])
        self.assertIn('/DSignedBuild', calls[2])
        self.assertTrue(any(arg.startswith('/SCBSSign=') and '$f' in arg for arg in calls[2]))
        self.assertEqual(calls[3][1:4], ['verify', '/pa', '/all'])
        self.assertIn(str(installer.resolve()), calls[3])
        self.assertTrue(installer.with_name(installer.name + '.sha256').is_file())

    def test_rejects_invalid_version_or_thumbprint(self):
        with patch('scripts.build_installer.sys.platform', 'win32'), \
             patch('scripts.build_installer.find_compiler', return_value=Path('ISCC.exe')):
            with self.assertRaises(ValueError):
                build_installer(self.exe, 'invalid', self.root)
            with self.assertRaises(ValueError):
                build_installer(self.exe, '1.1.0', self.root, 'invalid')
