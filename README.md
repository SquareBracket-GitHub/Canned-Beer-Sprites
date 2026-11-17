# canned beer sprites

Pack your images into a sprite sheet and export the coordinates as XML.

**canned beer sprites** is a local desktop tool for preparing game sprites, animation frames, icons, and other image assets. Add your files, choose a layout, preview the result, and click **Generate** to save a transparent PNG and its matching XML file.

No account, server, API key, or Photoshop installation is required. The interface is in English.

## 1. Key Features

- **Import files or folders** using the file picker or drag and drop. Folder imports include subfolders.
- **Manage your image list** by dragging entries to reorder them or removing selected entries.
- **Choose a layout:** Rows, Uniform grid, or Compact.
- **Control sheet size:** automatic sizing by default, with optional manual width and height.
- **Set spacing** between images in pixels.
- **Preview the sheet and XML** as the image list or settings change.
- **Export PNG + XML together**, with original image dimensions and transparency preserved.
- **Name sprites automatically** from filenames without extensions, adding numbers for duplicates.
- **See validation errors** in red below Generate. Successful export displays `well seamed!`.

## 2. Tech Stack

| Component | Technology |
| --- | --- |
| Language | Python 3.10+ |
| Desktop interface | PySide6 / Qt Widgets |
| Image composition | Qt QImage |
| XML generation | Python ElementTree |
| Packaging | pyside6-deploy / Nuitka |

The application processes images locally. There is no database or backend service.

## 3. Getting Started

### Download and run

Download the build for your computer from [Releases](https://github.com/SquareBracket-GitHub/Canned-Beer-Sprites/releases/latest). Python is included; no development environment or separate runtime installation is required.

| Your computer | Download |
| --- | --- |
| Windows 64-bit (Intel / AMD) | [Windows exe](https://github.com/SquareBracket-GitHub/Canned-Beer-Sprites/releases/download/v1.0.0/canned-beer-sprites-v1.0.0-windows-x64.exe) |
| Mac with Apple Silicon (M1 and newer) | [macOS arm64 zip](https://github.com/SquareBracket-GitHub/Canned-Beer-Sprites/releases/download/v1.0.0/canned-beer-sprites-v1.0.0-macos-arm64.zip) |
| Mac with Intel processor | [macOS x64 zip](https://github.com/SquareBracket-GitHub/Canned-Beer-Sprites/releases/download/v1.0.0/canned-beer-sprites-v1.0.0-macos-x64.zip) |

**Windows:** download the exe and run it. No installer is needed.

**macOS:** extract the zip, move **canned beer sprites.app** to Applications, and open it.

Mac builds use ad-hoc signing and are not Developer ID signed or notarized. If macOS blocks the first launch, use **System Settings > Privacy & Security > Open Anyway** for this downloaded app. Windows may show an unknown publisher warning because the executable has no publisher certificate.

The release pipeline builds each artifact on its target OS, runs the core tests, and checks packaged application startup. This does not replace full manual testing on every target computer. SHA-256 checksum files are included with the downloads.

### Run from source

Use Python 3.10 or newer; Python 3.12 was used for the initial build. Git is needed for the clone command.

```sh
git clone https://github.com/SquareBracket-GitHub/Canned-Beer-Sprites.git
cd Canned-Beer-Sprites
```

**macOS**

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m canned_beer.app
```

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m canned_beer.app
```

Run these commands from the repository root. Application startup does not require an `.env` file.

## 4. Usage

1. Click **Add files** or **Add folder**, or drop local files or folders onto the window.
2. Arrange the image list by dragging entries. Use **Remove selected** to remove images.
3. Choose **Layout**, sheet dimensions, and spacing.
4. Check **Sheet Preview** and the XML preview below it.
5. Set **Output name**, click **Generate**, and choose an output folder.
6. After both files are saved, the application displays **well seamed!**.

The default output files are:

```text
spritesheet.png
spritesheet.xml
```

If either output file already exists, the application asks before overwriting it. Original source images are not modified.

### Layouts

| Layout | Behavior |
| --- | --- |
| Rows | Places images in list order, moving to a new row when the current row is full. |
| Uniform grid | Uses cells sized to the widest and tallest input images. Images keep their original size and sit at the top-left of each cell. |
| Compact | Packs larger images first to reduce unused space. Placement can differ from list order. |

Compact uses a heuristic and does not guarantee the smallest possible sheet. Images are never rotated, resized, or trimmed.

### Options

| Option | Default | Description |
| --- | --- | --- |
| Layout | Rows | Select the packing method. |
| Sheet size / Automatic | Enabled | Chooses dimensions from the input images; the result need not be square or a power of two. |
| Width / Height | 1024 / 1024 | Manual sheet dimensions in pixels, used when Automatic is disabled. |
| Spacing | 0 | Gap between images, from 0 to 256 pixels; not an outer border or edge extrusion. |
| Output name | spritesheet | Base filename for both exported files. |

A sheet is limited to **16,384 pixels per side** and **64 megapixels total**. If the selected layout cannot fit the images on one sheet, Generate is disabled and a red message asks you to increase the sheet size. The application does not split output across multiple sheets.

### Image input

The file picker and folder importer accept PNG, JPG/JPEG, BMP, WebP, GIF, and TIF/TIFF. Decoding depends on the image plugins available in the installed or packaged Qt runtime. Unreadable files produce a warning.

Animated images are loaded as a single image; GIF animations are not extracted into separate frames. The same resolved file path is added only once. Files from different folders may share a filename.

### Sprite names

Names use the source filename without its extension. Duplicate names receive numeric suffixes in list order:

```text
idle.png        -> idle
idle.jpg        -> idle_2
another/idle.png -> idle_3
```

Names remain unique even when an input already has a suffix: adding `idle_2.png` after `idle` and `idle_2` produces `idle_2_2`.

### XML output

```xml
<?xml version='1.0' encoding='utf-8'?>
<TextureAtlas imagePath="spritesheet.png">
  <SubTexture name="idle" x="0" y="0" width="64" height="64" />
  <SubTexture name="idle_2" x="64" y="0" width="64" height="64" />
</TextureAtlas>
```

Each `SubTexture` includes `name`, `x`, `y`, `width`, and `height`. Coordinates are measured in pixels from the sheet's top-left corner, where `(0, 0)` is the origin. Width and height describe the original image bounds and exclude spacing. `imagePath` references the exported PNG filename.

Your engine or loader must support this XML structure or adapt it to its own format. Other metadata formats are not currently exported.

### Build an executable

Build on the target operating system, using Python 3.12. Do not copy virtual environments between operating systems. Install the project as described above, then install the build tools:

```sh
python -m pip install Nuitka==4.1.1 ordered-set==4.1.0 zstandard==0.25.0
python scripts/build.py
```

On Windows, use `.\.venv\Scripts\python.exe` instead of `python` if the environment is not activated. Windows builds require Visual Studio C++ Build Tools; macOS builds require the Xcode Command Line Tools.

No separate `main.py` is needed: `canned_beer/app.py` is the entry point. The script builds an executable, checks startup outside the source tree, and writes a release download plus SHA-256 checksum to `dist/release/`:

- Windows: a single `.exe` for x64.
- macOS: a `.zip` containing an app bundle for the build machine's architecture.

Windows onefile packaging extracts its bundled dependencies to a temporary directory at startup. macOS uses an application bundle, which Finder presents as one app.

The GitHub Actions **Build release** workflow builds Windows x64, macOS arm64, and macOS x64. It can be run manually for validation. Pushing a version tag publishes a release only after every platform build and startup check succeeds.

## 5. Project Structure

```text
canned_beer/
  __init__.py
  app.py              Desktop UI, preview, image composition, and export
  core.py             Sprite naming, packing, and XML generation
tests/
  test_core.py        Naming, layout bounds, spacing, overflow, and XML tests
pyproject.toml        Python package metadata and dependencies
pysidedeploy.spec     Alternative pyside6-deploy configuration
scripts/build.py     Native build, startup check, and release packaging
.github/workflows/
  release.yml        Cross-platform build and GitHub Release publishing
README.md
```

Generated builds are written to `dist/` and excluded from Git, along with virtual environments and `.env` files.

## 6. Contributing

Report bugs or suggest improvements through [GitHub Issues](https://github.com/SquareBracket-GitHub/Canned-Beer-Sprites/issues). Include your operating system, layout settings, image dimensions, and steps to reproduce the problem.

For code changes, fork the repository, create a branch, make a focused change, and open a pull request with a description and verification results.

Run the core tests from the repository root:

```sh
python -m unittest discover -s tests -v
```

These tests cover naming collisions, layout bounds and spacing, oversized inputs, and XML attributes. They do not replace testing the packaged app on each target OS.

## 7. Author & Contact

- **Author:** New Potato
- **GitHub:** [SquareBracket-GitHub](https://github.com/SquareBracket-GitHub)
- **Repository:** [Canned-Beer-Sprites](https://github.com/SquareBracket-GitHub/Canned-Beer-Sprites)

## 8. License

A project license has not yet been selected, and no project `LICENSE` file is included. Do not assume that this repository uses the license of another sprite-sheet tool.

PySide6, Qt, and other dependencies retain their own licenses; review their terms before distributing packaged builds.
