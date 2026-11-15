import os
import sys
import struct
import hashlib
from pathlib import Path

ENTRY_TITLE = "Galaxy Koi"


def parse_png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[12:16] != b"IHDR":
        sys.exit("Error: Invalid PNG header structure in art.jpg")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def parse_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    idx = 2
    data_len = len(data)
    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3,
        0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB,
        0xCD, 0xCE, 0xCF
    }

    while idx < data_len:
        if data[idx] != 0xFF:
            sys.exit("Error: Corrupt JPEG format in art.jpg")
        while idx < data_len and data[idx] == 0xFF:
            idx += 1
        if idx >= data_len:
            break
        marker = data[idx]
        idx += 1

        if marker in (0xD8, 0xD9, 0x01) or (0xD0 <= marker <= 0xD7):
            continue

        if idx + 2 > data_len:
            sys.exit("Error: Truncated JPEG marker header in art.jpg")

        length = struct.unpack(">H", data[idx:idx + 2])[0]
        if marker in sof_markers:
            if idx + length > data_len or length < 9:
                sys.exit("Error: Truncated SOF frame in art.jpg")
            height, width = struct.unpack(">HH", data[idx + 3:idx + 7])
            return width, height

        idx += length

    sys.exit("Error: Could not find SOF marker in JPEG art.jpg")


def validate_and_process():
    script_dir = Path(__file__).resolve().parent
    art_path = script_dir / "art.jpg"

    if not art_path.is_file():
        sys.exit("Error: missing required file art.jpg")

    data = art_path.read_bytes()
    byte_count = len(data)

    if byte_count > 1048576:
        sys.exit(f"Error: art.jpg size ({byte_count} bytes) exceeds maximum limit of 1048576 bytes")

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        if not data.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82"):
            sys.exit("Error: Truncated PNG file art.jpg (missing IEND chunk)")
        width, height = parse_png_dimensions(data)
    elif data.startswith(b"\xff\xd8"):
        if not data.endswith(b"\xff\xd9"):
            sys.exit("Error: Truncated JPEG file art.jpg (missing EOI marker)")
        width, height = parse_jpeg_dimensions(data)
    else:
        sys.exit("Error: Unsupported image format in art.jpg (must be PNG or JPEG)")

    if width <= 0 or height <= 0:
        sys.exit(f"Error: Invalid image dimensions {width}x{height} in art.jpg")

    if width > 1024 or height > 1024:
        sys.exit(f"Error: Image dimensions {width}x{height} in art.jpg exceed maximum limit of 1024x1024")

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = Path(out_dir) / "entry.png"
    out_path.write_bytes(data)

    digest = hashlib.sha256(data).hexdigest()[:16]
    print(f"Successfully processed {ENTRY_TITLE}: {width}x{height}, {byte_count} bytes, sha256:{digest}")


if __name__ == "__main__":
    validate_and_process()
