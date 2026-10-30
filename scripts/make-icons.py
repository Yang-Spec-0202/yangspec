#!/usr/bin/env python3
"""Rebuild the site icons from the GitHub avatar.

Source: https://avatars.githubusercontent.com/u/123146308?v=4 (Yang-Spec-0202)
Usage:  python3 scripts/make-icons.py path/to/avatar.jpg

Writes favicon.ico, favicon-16x16.png, favicon-32x32.png, apple-touch-icon.png
and avatar-128.png into static/.

Favicons use a tighter centre crop than the header mark: at 16 px the full frame
turns into a blue smudge, while the cropped face keeps both eyes readable.
"""
import io
import struct
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

FAVICON_CROP = 0.78  # share of the frame kept for favicons
HEADER_CROP = 1.0    # header mark keeps the whole avatar


def square(im: Image.Image, keep: float) -> Image.Image:
    """Centre-crop `keep` of the shortest side."""
    w, h = im.size
    side = int(min(w, h) * keep)
    left = (w - side) // 2
    top = (h - side) // 2
    return im.crop((left, top, left + side, top + side))


def resized(im: Image.Image, size: int, sharpen: bool = False) -> Image.Image:
    out = im.resize((size, size), Image.LANCZOS)
    if sharpen:
        out = out.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=2))
        out = ImageEnhance.Contrast(out).enhance(1.08)
    return out


def write_ico(path: Path, frames: list[tuple[int, Image.Image]]) -> None:
    """Write a multi-size ICO with PNG payloads (Pillow only emits one frame)."""
    pngs = []
    for size, im in frames:
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        pngs.append((size, buf.getvalue()))
    entries = b""
    data = b""
    offset = 6 + 16 * len(pngs)
    for size, blob in pngs:
        entries += struct.pack(
            "<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(blob), offset
        )
        offset += len(blob)
        data += blob
    path.write_bytes(struct.pack("<HHH", 0, 1, len(pngs)) + entries + data)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    source = Image.open(sys.argv[1]).convert("RGB")
    icon = square(source, FAVICON_CROP)

    resized(icon, 16, sharpen=True).save(STATIC / "favicon-16x16.png")
    resized(icon, 32, sharpen=True).save(STATIC / "favicon-32x32.png")
    resized(icon, 180).save(STATIC / "apple-touch-icon.png")
    square(source, HEADER_CROP).resize((128, 128), Image.LANCZOS).save(
        STATIC / "avatar-128.png"
    )

    write_ico(
        STATIC / "favicon.ico",
        [(size, resized(icon, size, sharpen=True)) for size in (16, 32, 48)],
    )
    print("icons written to", STATIC)


if __name__ == "__main__":
    main()
