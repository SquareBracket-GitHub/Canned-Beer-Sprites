"""Package the Windows executable as a per-user installer with shortcuts."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def find_compiler():
    if os.environ.get('ISCC'):
        return Path(os.environ['ISCC'])
    if shutil.which('iscc'):
        return Path(shutil.which('iscc'))
    for variable in ('ProgramFiles(x86)', 'ProgramFiles'):
        base = Path(os.environ.get(variable, 'C:/Program Files'))
        for version in ('7', '6'):
            compiler = base / f'Inno Setup {version}' / 'ISCC.exe'
            if compiler.is_file():
                return compiler
    raise SystemExit('Inno Setup is required. Install it or set ISCC to ISCC.exe.')


def find_signtool():
    if os.environ.get('SIGNTOOL'):
        return Path(os.environ['SIGNTOOL'])
    if shutil.which('signtool'):
        return Path(shutil.which('signtool'))
    kits = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Windows Kits/10/bin'
    tools = sorted(kits.glob('*/x64/signtool.exe'))
    if tools:
        return tools[-1]
    raise SystemExit('Windows SDK SignTool is required for signed builds.')


def build_installer(executable, version, output_dir, certificate_thumbprint=None,
                    require_signature=False):
    if sys.platform != 'win32':
        raise SystemExit('Windows installer builds must run on Windows.')
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Version must have the form major.minor.patch.')
    executable = Path(executable).resolve()
    output_dir = Path(output_dir).resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)
    if require_signature and not certificate_thumbprint:
        raise ValueError('A code signing certificate is required; refusing an unsigned build.')
    output_dir.mkdir(parents=True, exist_ok=True)
    args = [str(find_compiler()), f'/DAppVersion={version}',
            f'/DSourceExe={executable}', f'/DReleaseDir={output_dir}',
            f'/DAppIcon={ROOT / "assets/cbs.ico"}']
    signtool = None
    if certificate_thumbprint:
        if not re.fullmatch(r'[0-9a-fA-F]{40}', certificate_thumbprint):
            raise ValueError('Certificate thumbprint must contain 40 hexadecimal characters.')
        signtool = str(find_signtool())
        signing = [signtool, 'sign', '/sha1', certificate_thumbprint,
                   '/fd', 'sha256', '/tr', 'http://timestamp.digicert.com', '/td', 'sha256']
        # The private key stays in the Windows certificate store or its HSM provider.
        subprocess.run(signing + [str(executable)], check=True)
        subprocess.run([signtool, 'verify', '/pa', '/all', str(executable)], check=True)
        args += ['/DSignedBuild',
                 f'/SCBSSign=$q{signtool}$q sign /sha1 {certificate_thumbprint} '
                 '/fd sha256 /tr http://timestamp.digicert.com /td sha256 $f']
    args.append(str(ROOT / 'scripts/windows-installer.iss'))
    subprocess.run(args, check=True)
    installer = output_dir / f'canned-beer-sprites-v{version}-windows-x64-setup.exe'
    if signtool:
        subprocess.run([signtool, 'verify', '/pa', '/all', str(installer)], check=True)
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    installer.with_name(installer.name + '.sha256').write_text(
        f'{digest}  {installer.name}\n', encoding='utf-8')
    print(f'Installer created ({"signed" if signtool else "unsigned"}): {installer}')
    return installer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist/release')
    parser.add_argument('--certificate-thumbprint', help='Code signing certificate in CurrentUser/My')
    parser.add_argument('--require-signature', action='store_true')
    options = parser.parse_args()
    build_installer(options.executable, options.version, options.output_dir,
                    options.certificate_thumbprint, options.require_signature)


if __name__ == '__main__':
    main()
