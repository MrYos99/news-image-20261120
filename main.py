#!/usr/bin/env python3
"""news-image-20261120 entry: copy the composed front page to /output/entry.png.

The front page is composed at build time (see compose.py in the build
session) and held in this repository as entry.png. The grader runs this
program with no network and standard library only, so the program verifies
the image (format, dimensions, size cap) and copies it unchanged.
Deterministic: the same input bytes produce the same output bytes, so the
two grading runs write identical files.
"""
import hashlib
import os
import struct
import sys

EXPECTED_W, EXPECTED_H = 1024, 1024
MAX_BYTES = 1_048_576  # 1 MiB


def _jpeg_dimensions(data):
    """Scan JPEG markers for the SOF0/SOF2 frame; return (w, h) or None."""
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h = struct.unpack(">H", data[i + 5:i + 7])[0]
            w = struct.unpack(">H", data[i + 7:i + 9])[0]
            return w, h
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        size = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + size
    return None


def _png_dimensions(data):
    if len(data) < 33 or data[12:16] != b"IHDR":
        return None
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def verify(data):
    """Return (format, w, h); raise SystemExit with a message on failure."""
    if len(data) > MAX_BYTES:
        sys.exit(f"entry image is {len(data)} bytes, over the 1 MiB cap")
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        fmt, dims = "PNG", _png_dimensions(data)
    elif data[:3] == b"\xff\xd8\xff":
        fmt, dims = "JPEG", _jpeg_dimensions(data)
    else:
        sys.exit("entry image is neither PNG nor JPEG (bad magic bytes)")
    if dims is None:
        sys.exit(f"could not read {fmt} dimensions")
    w, h = dims
    if (w, h) != (EXPECTED_W, EXPECTED_H):
        sys.exit(f"entry image is {w}x{h}, expected "
                 f"{EXPECTED_W}x{EXPECTED_H}")
    return fmt, w, h


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    with open(src, "rb") as fh:
        data = fh.read()
    fmt, w, h = verify(data)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    with open(dst, "wb") as fh:
        fh.write(data)

    # Round-trip check: what we wrote is byte-identical to what we read,
    # and it still verifies as a 1024x1024 image under the 1 MiB cap.
    with open(dst, "rb") as fh:
        written = fh.read()
    if hashlib.sha256(written).hexdigest() != hashlib.sha256(data).hexdigest():
        sys.exit("output differs from source after copy")
    verify(written)
    print(f"wrote {dst}: {fmt} {w}x{h}, {len(data)} bytes, "
          f"sha256 {hashlib.sha256(data).hexdigest()[:16]}...")


if __name__ == "__main__":
    main()
