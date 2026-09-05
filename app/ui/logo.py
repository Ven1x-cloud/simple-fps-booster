"""Logo: vector neon emblem (canvas) + PNG loader."""
import math
import os

from .. import theme as T


def _hex_points(cx, cy, r):
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 30)
        pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


def draw_logo(canvas, size, accent=T.ACCENT, dim=T.ACCENT_DIM, tags="logo"):
    """Draw the vector emblem centered in a `size` x `size` canvas."""
    canvas.delete(tags)
    s = float(size)
    cx = cy = s / 2.0
    lw = max(2, int(round(s * 0.055)))
    canvas.create_polygon(_hex_points(cx, cy, s * 0.46),
                          outline=accent, fill="", width=lw, tags=tags)
    canvas.create_polygon(_hex_points(cx, cy, s * 0.35),
                          outline=dim, fill="", width=max(1, lw // 2), tags=tags)
    cw = max(2, int(round(s * 0.07)))
    canvas.create_line(s * 0.32, s * 0.60, s * 0.50, s * 0.38,
                       s * 0.68, s * 0.60,
                       fill=accent, width=cw, capstyle="projecting",
                       joinstyle="miter", tags=tags)
    canvas.create_line(s * 0.38, s * 0.72, s * 0.62, s * 0.72,
                       fill=dim, width=max(1, lw // 2), tags=tags)
    r = s * 0.032
    canvas.create_oval(s * 0.5 - r, s * 0.20 - r, s * 0.5 + r, s * 0.20 + r,
                       fill=accent, outline="", tags=tags)


def asset_logo_path():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base, "assets", "logo.png")
    return p if os.path.isfile(p) else None


def load_logo_image(path, size):
    """Load the PNG logo (Pillow preferred for exact sizing). Returns PhotoImage or None."""
    try:
        from PIL import Image, ImageTk
        im = Image.open(path).convert("RGBA")
        im = im.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(im)
    except Exception:
        try:
            from tkinter import PhotoImage
            return PhotoImage(file=path)
        except Exception:
            return None
