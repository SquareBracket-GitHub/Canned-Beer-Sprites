"""Create an unsigned Store submission MSIX or a clearly marked preview."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = 'http://schemas.microsoft.com/appx/manifest/foundation/windows10'
UAP = 'http://schemas.microsoft.com/appx/manifest/uap/windows10'
RESCAP = 'http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities'
ET.register_namespace('', FOUNDATION)
ET.register_namespace('uap', UAP)
ET.register_namespace('rescap', RESCAP)


def find_makeappx():
    if os.environ.get('MAKEAPPX'):
        return Path(os.environ['MAKEAPPX'])
    if shutil.which('makeappx'):
        return Path(shutil.which('makeappx'))
    kits = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Windows Kits/10/bin'
    tools = sorted(kits.glob('*/x64/makeappx.exe'))
    if tools:
        return tools[-1]
    raise SystemExit('Windows SDK MakeAppx is required; install the SDK or set MAKEAPPX.')


def create_manifest(version, identity_name, publisher, publisher_display_name, preview=False):
    if not re.fullmatch(r'\d+\.\d+\.\d+\.0', version):
        raise ValueError('Use a four-part Store version ending in .0, for example 1.1.0.0.')
    if any(int(part) > 65535 for part in version.split('.')) or int(version.split('.')[0]) == 0:
        raise ValueError('Version components must be at most 65535, with a nonzero major version.')
    if not re.fullmatch(r'[A-Za-z0-9.-]{3,50}', identity_name):
        raise ValueError('Package identity must contain 3–50 letters, digits, dots or hyphens.')
    if not publisher.startswith('CN=') or not publisher_display_name.strip():
        raise ValueError('Supply the Publisher and PublisherDisplayName from Partner Center.')
    name = 'Canned Beer Sprites Preview' if preview else 'Canned Beer Sprites'
    package = ET.Element(f'{{{FOUNDATION}}}Package', IgnorableNamespaces='uap rescap')
    ET.SubElement(package, f'{{{FOUNDATION}}}Identity', Name=identity_name,
                  Publisher=publisher, Version=version, ProcessorArchitecture='x64')
    properties = ET.SubElement(package, f'{{{FOUNDATION}}}Properties')
    for tag, text in [('DisplayName', name), ('PublisherDisplayName', publisher_display_name),
                      ('Description', 'Pack images into a transparent PNG sprite sheet and XML.'),
                      ('Logo', 'Assets/StoreLogo.png')]:
        ET.SubElement(properties, f'{{{FOUNDATION}}}{tag}').text = text
    resources = ET.SubElement(package, f'{{{FOUNDATION}}}Resources')
    ET.SubElement(resources, f'{{{FOUNDATION}}}Resource', Language='en-us')
    dependencies = ET.SubElement(package, f'{{{FOUNDATION}}}Dependencies')
    ET.SubElement(dependencies, f'{{{FOUNDATION}}}TargetDeviceFamily',
                  Name='Windows.Desktop', MinVersion='10.0.17763.0', MaxVersionTested='10.0.26100.0')
    applications = ET.SubElement(package, f'{{{FOUNDATION}}}Applications')
    application = ET.SubElement(applications, f'{{{FOUNDATION}}}Application', Id='CBS',
                                Executable='app/canned-beer-sprites.exe', EntryPoint='Windows.FullTrustApplication')
    ET.SubElement(application, f'{{{UAP}}}VisualElements', DisplayName=name,
                  Description='Sprite sheet and XML desktop tool', BackgroundColor='#34495E',
                  Square150x150Logo='Assets/Square150x150Logo.png',
                  Square44x44Logo='Assets/Square44x44Logo.png')
    capabilities = ET.SubElement(package, f'{{{FOUNDATION}}}Capabilities')
    ET.SubElement(capabilities, f'{{{RESCAP}}}Capability', Name='runFullTrust')
    ET.indent(package)
    return ET.tostring(package, encoding='utf-8', xml_declaration=True)


def build_msix(executable, version, output_dir, identity_name=None, publisher=None,
               publisher_display_name=None, preview=False):
    if sys.platform != 'win32':
        raise SystemExit('MSIX packaging must run on Windows.')
    if preview:
        if any((identity_name, publisher, publisher_display_name)):
            raise ValueError('Preview uses its own identity; omit Store identity arguments.')
        identity_name = 'CBS.CannedBeerSprites.Preview'
        publisher = 'CN=CBS Preview'
        publisher_display_name = 'CBS Preview'
    elif not all((identity_name, publisher, publisher_display_name)):
        raise ValueError('Store identity Name, Publisher, and PublisherDisplayName are all required.')
    manifest = create_manifest(version, identity_name, publisher, publisher_display_name, preview)
    executable = Path(executable).resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    channel = 'preview' if preview else 'store'
    artifact = output_dir / f'canned-beer-sprites-v{version}-windows-x64-{channel}.msix'
    if artifact.exists():
        raise FileExistsError(f'Refusing to overwrite an existing package: {artifact}')
    with tempfile.TemporaryDirectory(prefix='cbs-msix-') as temp:
        staging = Path(temp)
        (staging / 'app').mkdir()
        (staging / 'Assets').mkdir()
        shutil.copy2(executable, staging / 'app/canned-beer-sprites.exe')
        (staging / 'AppxManifest.xml').write_bytes(manifest)
        logo = QImage(str(ROOT / 'canned_beer/resources/cbs.png'))
        if logo.isNull():
            raise RuntimeError('Application logo is missing or unreadable.')
        for name, size in [('StoreLogo', 50), ('Square44x44Logo', 44), ('Square150x150Logo', 150)]:
            image = logo.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
            if not image.save(str(staging / f'Assets/{name}.png')):
                raise RuntimeError(f'Could not write {name}.png')
        subprocess.run([str(find_makeappx()), 'pack', '/d', str(staging), '/p', str(artifact)], check=True)
    with zipfile.ZipFile(artifact) as package:
        if package.read('app/canned-beer-sprites.exe') != executable.read_bytes():
            raise RuntimeError('Packaged application does not match the source executable.')
        identity = ET.fromstring(package.read('AppxManifest.xml')).find(f'{{{FOUNDATION}}}Identity')
        if identity.attrib['Name'] != identity_name or identity.attrib['Publisher'] != publisher:
            raise RuntimeError('Packaged identity does not match the requested identity.')
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    artifact.with_name(artifact.name + '.sha256').write_text(
        f'{digest}  {artifact.name}\n', encoding='utf-8')
    print(f'Created unsigned {channel} package: {artifact}')
    print('Preview is not installable or Store-ready.' if preview else
          'For Partner Center submission; Store signs it after certification. Direct download requires separate signing.')
    return artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist/store')
    parser.add_argument('--identity-name')
    parser.add_argument('--publisher')
    parser.add_argument('--publisher-display-name')
    parser.add_argument('--preview', action='store_true')
    options = parser.parse_args()
    build_msix(options.executable, options.version, options.output_dir, options.identity_name,
               options.publisher, options.publisher_display_name, options.preview)


if __name__ == '__main__':
    main()
