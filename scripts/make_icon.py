#!/usr/bin/env python3
"""Generate assets/app.ico from assets/logo.png (requires Pillow)."""
import os
import sys


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(base, "assets", "logo.png")
    out = os.path.join(base, "assets", "app.ico")
    if not os.path.isfile(src):
        print(f"logo not found: {src}")
        return 1
    try:
        from PIL import Image
    except Exception as e:
        print(f"Pillow required: {e}")
        return 1
    im = Image.open(src).convert("RGBA")
    im.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                        (64, 64), (128, 128), (256, 256)])
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
