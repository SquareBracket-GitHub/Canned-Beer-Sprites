"""Convert the final assets/cbs.png artwork to native icon formats."""
from pathlib import Path
import struct

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = QImage(str(ROOT / "assets" / "cbs.png"))
    if source.isNull() or source.width() != source.height():
        raise SystemExit("assets/cbs.png must be a readable square image.")

    def png(size):
        scaled = source.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not scaled.save(buffer, "PNG"):
            raise RuntimeError("Could not encode icon PNG.")
        return bytes(data)

    sizes = (16, 24, 32, 48, 64, 128, 256)
    payloads = [png(size) for size in sizes]
    offset = 6 + 16 * len(sizes)
    entries = []
    for size, payload in zip(sizes, payloads):
        entries.append(struct.pack("<BBBBHHII", size % 256, size % 256,
                                   0, 0, 1, 32, len(payload), offset))
        offset += len(payload)
    (ROOT / "assets" / "cbs.ico").write_bytes(
        struct.pack("<HHH", 0, 1, len(sizes)) + b"".join(entries + payloads))

    chunks = []
    for kind, size in ((b"icp4", 16), (b"icp5", 32), (b"icp6", 64),
                       (b"ic07", 128), (b"ic08", 256), (b"ic09", 512),
                       (b"ic10", 1024)):
        payload = png(size)
        chunks.append(kind + struct.pack(">I", len(payload) + 8) + payload)
    body = b"".join(chunks)
    (ROOT / "assets" / "cbs.icns").write_bytes(
        b"icns" + struct.pack(">I", len(body) + 8) + body)

    resources = ROOT / "canned_beer" / "resources"
    resources.mkdir(exist_ok=True)
    (resources / "cbs.png").write_bytes(png(256))
    print("Generated Windows, macOS, and application window icons.")


if __name__ == "__main__":
    main()
