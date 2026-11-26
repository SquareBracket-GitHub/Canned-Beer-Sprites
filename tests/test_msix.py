from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from scripts.build_msix import create_manifest, build_msix, FOUNDATION, RESCAP


class MsixTests(unittest.TestCase):
    def test_store_identity_and_full_trust_manifest(self):
        manifest = create_manifest('1.1.0.0', 'Example.CBS', 'CN=Example & Team', 'Example & Team')
        root = ET.fromstring(manifest)
        identity = root.find(f'{{{FOUNDATION}}}Identity')
        self.assertEqual(identity.attrib['Publisher'], 'CN=Example & Team')
        self.assertEqual(identity.attrib['Name'], 'Example.CBS')
        self.assertEqual(identity.attrib['Version'], '1.1.0.0')
        app = root.find(f'{{{FOUNDATION}}}Applications/{{{FOUNDATION}}}Application')
        self.assertEqual(app.attrib['Executable'], 'app/canned-beer-sprites.exe')
        self.assertEqual(app.attrib['EntryPoint'], 'Windows.FullTrustApplication')
        capability = root.find(f'{{{FOUNDATION}}}Capabilities/{{{RESCAP}}}Capability')
        self.assertEqual(capability.attrib['Name'], 'runFullTrust')

    def test_no_store_build_without_registered_identity(self):
        with patch('scripts.build_msix.sys.platform', 'win32'):
            with self.assertRaisesRegex(ValueError, 'all required'):
                build_msix(Path('missing.exe'), '1.1.0.0', Path('dist/store'))
            with self.assertRaisesRegex(ValueError, 'omit Store identity'):
                build_msix(Path('missing.exe'), '1.1.0.0', Path('dist/store'),
                           identity_name='Example.CBS', preview=True)

    def test_invalid_store_versions_are_rejected(self):
        for version in ('1.1.0', '1.1.0.1', '0.1.0.0', '70000.1.0.0'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                create_manifest(version, 'Example.CBS', 'CN=Example', 'Example')
