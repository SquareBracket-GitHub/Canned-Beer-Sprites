"""Build and smoke-test a native release artifact on the current OS."""
import hashlib
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.1.0"


def main():
    os.chdir(ROOT)
    if sys.platform not in {"win32", "darwin"}:
        raise SystemExit("Release builds support Windows and macOS.")
    out = ROOT / "build" / "native"
    release = ROOT / "dist" / "release"
    out.mkdir(parents=True, exist_ok=True)
    release.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, "-m", "nuitka", "canned_beer/app.py",
            "--enable-plugin=pyside6", "--include-package=canned_beer",
            "--include-package-data=canned_beer",
            "--assume-yes-for-downloads", "--noinclude-qt-translations",
            f"--output-dir={out}", "--output-filename=canned-beer-sprites",
            "--jobs=3"]
    if sys.platform == "win32":
        args += ["--onefile", "--windows-console-mode=disable", "--msvc=latest",
                 f"--product-version={VERSION}", f"--file-version={VERSION}",
                 "--product-name=canned beer sprites",
                 f"--windows-icon-from-ico={ROOT / 'assets' / 'cbs.ico'}"]
    else:
        args += ["--standalone", "--macos-create-app-bundle",
                 "--macos-app-name=canned beer sprites",
                 "--macos-signed-app-name=com.squarebracket.cannedbeersprites",
                 f"--macos-app-version={VERSION}",
                 f"--macos-app-icon={ROOT / 'assets' / 'cbs.icns'}"]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    subprocess.run(args, check=True, env=env)
    if sys.platform == "win32":
        executable = out / "canned-beer-sprites.exe"
        artifact = release / "canned-beer-sprites-v1.1.0-windows-x64.exe"
        shutil.copy2(executable, artifact)
        executable = artifact
    else:
        bundle = out / "canned beer sprites.app"
        if bundle.exists():
            shutil.rmtree(bundle)
        (out / "app.app").rename(bundle)
        info = plistlib.loads((bundle / "Contents/Info.plist").read_bytes())
        executable = bundle / "Contents/MacOS" / info["CFBundleExecutable"]
        arch = "arm64" if platform.machine() == "arm64" else "x64"
        artifact = release / f"canned-beer-sprites-v1.1.0-macos-{arch}.zip"
    # Run the bundled application outside the source tree without PYTHONPATH.
    smoke_env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    smoke_env.pop("PYTHONPATH", None)
    subprocess.run([str(executable), "--smoke-test"], cwd=out,
                   env=smoke_env, check=True, timeout=120)
    if sys.platform == "darwin":
        # ditto preserves executable permissions, symlinks, and bundle metadata.
        subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
                        str(bundle), str(artifact)], check=True)
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    artifact.with_name(artifact.name + ".sha256").write_text(
        f"{digest}  {artifact.name}\n", encoding="utf-8")
    print(f"Verified release artifact: {artifact}")


if __name__ == "__main__":
    main()
