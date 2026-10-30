#!/usr/bin/env python3
"""Rebuild the site icons from the GitHub avatar.

Source: https://avatars.githubusercontent.com/u/123146308?v=4 (Yang-Spec-0202)
Usage:  python3 scripts/make-icons.py path/to/avatar.jpg
Writes favicon.ico, favicon-16x16.png, favicon-32x32.png, apple-touch-icon.png,
favicon.svg and avatar-128.png into static/.
"""
import base64
import io
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"


def square(im: Image.Image) -> Image.Image:
    """Center-crop to a square so non-square uploads stay proportional."""
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return im.crop((left, top, left + side, top + side))


def resized(im: Image.Image, size: int, sharpen: bool = False) -> Image.Image:
    out = im.resize((size, size), Image.LANCZOS)
    if sharpen:
        out = out.filter(ImageFilter.UnsharpMask(radius=1, percent=60, threshold=2))
    return out


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = square(Image.open(sys.argv[1]).convert("RGB"))

    resized(src, 16, sharpen=True).save(STATIC / "favicon-16x16.png")
    resized(src, 32).save(STATIC / "favicon-32x32.png")
    resized(src, 180).save(STATIC / "apple-touch-icon.png")
    resized(src, 128).save(STATIC / "avatar-128.png")

    ico = [resized(src, s) for s in (16, 32, 48)]
    ico[0].save(
        STATIC / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=ico[1:],
    )

    buf = io.BytesIO()
    resized(src, 64).save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    (STATIC / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="YangSpec">'
        f'<image width="64" height="64" href="data:image/png;base64,{b64}"/>'
        "</svg>\n",
        encoding="utf-8",
    )
    print("icons written to", STATIC)


if __name__ == "__main__":
    main()
