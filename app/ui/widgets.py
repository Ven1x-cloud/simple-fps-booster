"""Reusable neon widgets: cards, buttons, toggles, gauges, charts, bars."""
import tkinter as tk
from tkinter import font as tkfont

from .. import theme as T


def round_rect(c, x1, y1, x2, y2, r=10, **kw):
    """Draw a rounded rectangle on a canvas. Returns the item id."""
    r = max(0, min(r, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return c.create_polygon(pts, smooth=True, **kw)


def font(size=11, bold=False, mono=False):
    fam = T.FAMILY_MONO if mono else T.FAMILY
    return tkfont.Font(family=fam, size=size, weight="bold" if bold else "normal")


def text_width(f, text):
    try:
        return f.measure(text)
    except Exception:
        return len(text) * 8


class Card(tk.Frame):
    """Flat card: 1px border + accent top strip. Children go in .body."""

    def __init__(self, master, accent=None, pad=14, **kw):
        super().__init__(master, bg=T.BG1,
                         highlightbackground=T.BORDER,
                         highlightcolor=T.BORDER_HI,
                         highlightthickness=1, **kw)
        strip = tk.Frame(self, bg=accent or T.ACCENT_DIM, height=2)
        strip.pack(fill="x")
        strip.pack_propagate(False)
        self.body = tk.Frame(self, bg=T.BG1)
        self.body.pack(fill="both", expand=True, padx=pad, pady=pad - 3)


class CardTitle(tk.Label):
    def __init__(self, master, text, **kw):
        super().__init__(master, text=text, bg=T.BG1, fg=T.TEXT_DIM,
                         font=font(10, bold=True), **kw)


class NeonButton(tk.Canvas):
    """Rounded canvas button with hover state. Styles: primary/ghost/accent/danger."""

    STYLES = {
        "primary": {"bg": T.ACCENT, "fg": "#03130b",
                    "bg_hov": T.ACCENT_SOFT, "border": T.ACCENT},
        "ghost": {"bg": T.BG2, "fg": T.TEXT,
                  "bg_hov": T.BG3, "border": T.BORDER_HI},
        "accent": {"bg": T.ACCENT_BG, "fg": T.ACCENT,
                   "bg_hov": T.ACCENT_DIM, "border": T.ACCENT_DIM},
        "danger": {"bg": T.DANGER_BG, "fg": T.DANGER,
                   "bg_hov": T.DANGER_HOVER, "border": T.DANGER_BORDER},
    }

    def __init__(self, master, text, command=None, style="ghost", size=11,
                 bold=True, padx=20, pady=9, radius=10, **kw):
        self._font = font(size, bold)
        self._style = self.STYLES.get(style, self.STYLES["ghost"])
        self._command = command
        self._enabled = True
        self._hover = False
        self._text = text
        self._padx, self._pady, self._radius = padx, pady, radius
        self._w = text_width(self._font, text) + padx * 2
        self._h = self._font.metrics("linespace") + pady * 2
        super().__init__(master, width=self._w, height=self._h,
                         bg=master.cget("bg"), highlightthickness=0, **kw)
        self._draw()
        self.bind("<Enter>", lambda e: self._hover_set(True))
        self.bind("<Leave>", lambda e: self._hover_set(False))
        self.bind("<Button-1>", self._on_click)

    def _hover_set(self, v):
        if self._hover != v:
            self._hover = v
            self._draw()

    def _on_click(self, event):
        if not self._enabled or not self._command:
            return
        try:
            self._command()
        except Exception as e:
            try:
                self.event_generate("<<ButtonError>>", when="tail", data=str(e))
            except Exception:
                pass

    def _draw(self):
        self.delete("all")
        s = self._style
        if self._enabled:
            bg = s["bg_hov"] if self._hover else s["bg"]
            fg, border = s["fg"], s["border"]
        else:
            bg, fg, border = T.BG1, T.TEXT_FAINT, T.BORDER
        round_rect(self, 1, 1, self._w - 1, self._h - 1, self._radius,
                   fill=bg, outline=border, width=1)
        self.create_text(self._w / 2, self._h / 2,
                         text=self._text, fill=fg, font=self._font)

    def set_text(self, text):
        if text == self._text:
            return
        self._text = text
        self._w = max(self._w, text_width(self._font, text) + self._padx * 2)
        self.config(width=self._w)
        self._draw()

    def set_enabled(self, v):
        self._enabled = bool(v)
        self._draw()


class Toggle(tk.Canvas):
    """Pill switch. command(value) fires on user click."""

    def __init__(self, master, value=False, command=None, width=46, height=24):
        self._value = bool(value)
        self._command = command
        self._w, self._h = width, height
        super().__init__(master, width=width, height=height,
                         bg=master.cget("bg"), highlightthickness=0,
                         cursor="hand2")
        self._draw()
        self.bind("<Button-1>", self._click)

    def _click(self, e):
        self.set(not self._value, fire=False)
        if self._command:
            try:
                self._command(self._value)
            except Exception:
                pass

    def get(self):
        return self._value

    def set(self, value, fire=True):
        self._value = bool(value)
        self._draw()
        if fire and self._command:
            try:
                self._command(self._value)
            except Exception:
                pass

    def _draw(self):
        self.delete("all")
        on = self._value
        pill = T.ACCENT if on else T.BG3
        border = T.ACCENT if on else T.BORDER_HI
        round_rect(self, 1, 1, self._w - 1, self._h - 1, self._h / 2 - 1,
                   fill=pill, outline=border, width=1)
        r = self._h / 2 - 4
        cx = (self._w - r - 5) if on else (r + 5)
        self.create_oval(cx - r, self._h / 2 - r, cx + r, self._h / 2 + r,
                         fill="#eafff2" if on else T.TEXT_FAINT, outline="")


class StatBar(tk.Canvas):
    """Horizontal 0-100 meter."""

    def __init__(self, master, w=150, h=8, color=T.ACCENT):
        super().__init__(master, width=w, height=h,
                         bg=master.cget("bg"), highlightthickness=0)
        self._w, self._h, self._color = w, h, color
        self._val = 0.0
        self._draw()

    def set(self, val):
        try:
            self._val = max(0.0, min(100.0, float(val)))
        except Exception:
            self._val = 0.0
        self._draw()

    def _draw(self):
        self.delete("all")
        round_rect(self, 0, 0, self._w - 1, self._h - 1, self._h / 2,
                   fill=T.BG3, outline="")
        w = self._w * self._val / 100.0
        if w > 5:
            round_rect(self, 0, 0, w, self._h - 1, self._h / 2,
                       fill=self._color, outline="")


class Gauge(tk.Canvas):
    """270-degree arc gauge with big center value."""

    def __init__(self, master, size=168, max_value=1000, label="", color=T.ACCENT):
        self._size = size
        self._max = max_value
        self._value = 0
        self._label = label
        self._color = color
        self._f_num = font(int(size * 0.21), True, mono=True)
        self._f_lab = font(max(8, int(size * 0.07)), bold=True)
        super().__init__(master, width=size, height=size,
                         bg=master.cget("bg"), highlightthickness=0)
        self._draw()

    def set(self, value, label=None):
        self._value = value
        if label is not None:
            self._label = label
        self._draw()

    def _draw(self):
        c = self
        s = self._size
        c.delete("all")
        lw = max(10, s // 15)
        x1, y1 = lw / 2, lw / 2
        x2, y2 = s - lw / 2, s - lw / 2
        c.create_arc(x1, y1, x2, y2, start=135, extent=270,
                     style="arc", outline=T.BG3, width=lw)
        ratio = 0.0
        if self._max > 0:
            ratio = max(0.0, min(1.0, self._value / self._max))
        ext = 270 * ratio
        if ext > 1:
            c.create_arc(x1, y1, x2, y2, start=135, extent=ext,
                         style="arc", outline=T.ACCENT_DIM, width=lw + 5)
            c.create_arc(x1, y1, x2, y2, start=135, extent=ext,
                         style="arc", outline=self._color, width=lw)
        c.create_text(s / 2, s / 2 - s * 0.05,
                      text=f"{int(round(self._value))}",
                      fill=T.TEXT, font=self._f_num)
        c.create_text(s / 2, s / 2 + s * 0.17,
                      text=str(self._label).upper(),
                      fill=T.TEXT_DIM, font=self._f_lab)


class LineChart(tk.Canvas):
    """Live line chart with auto-scaling, grid and trailing value label."""

    def __init__(self, master, w=420, h=190, samples=90, color=T.ACCENT, unit=""):
        self._w, self._h = w, h
        self._samples = samples
        self._color = color
        self._unit = unit
        self._data = []
        self._f_last = font(10, True, mono=True)
        self._f_minmax = font(8, mono=True)
        super().__init__(master, width=w, height=h, bg=T.BG1,
                         highlightthickness=0)
        self._draw()

    def push(self, v):
        try:
            self._data.append(float(v))
        except Exception:
            return
        if len(self._data) > self._samples:
            self._data.pop(0)
        self._draw()

    def resize(self, w, h):
        if w > 60 and h > 60 and (int(w) != self._w or int(h) != self._h):
            self._w, self._h = int(w), int(h)
            self.config(width=self._w, height=self._h)
            self._draw()

    def clear_data(self):
        self._data = []
        self._draw()

    def _draw(self):
        c = self
        c.delete("all")
        pad_l, pad_r, pad_t, pad_b = 6, 6, 20, 8
        w, h = self._w, self._h
        if w < 40 or h < 40:
            return
        data = self._data
        lo, hi = 0.0, 100.0
        if data:
            lo, hi = min(data), max(data)
            span = max(hi - lo, 1.0)
            lo = max(0.0, lo - span * 0.25)
            hi = hi + span * 0.25
        if hi <= lo:
            hi = lo + 1.0
        span = hi - lo
        steps = 4
        for i in range(steps + 1):
            gy = pad_t + (h - pad_t - pad_b) * i / steps
            c.create_line(pad_l, gy, w - pad_r, gy, fill=T.BORDER, dash=(2, 4))
        if len(data) >= 2:
            n = self._samples
            pts = []
            for idx, v in enumerate(data):
                x = pad_l + (w - pad_l - pad_r) * idx / max(1, n - 1)
                y = pad_t + (h - pad_t - pad_b) * (1.0 - (v - lo) / span)
                pts += [x, y]
            c.create_polygon(pts + [w - pad_r, h - pad_b, pad_l, h - pad_b],
                             fill=T.ACCENT_BG, outline="")
            c.create_line(pts, fill=self._color, width=2, smooth=True)
            lx, ly = pts[-2], pts[-1]
            c.create_oval(lx - 3.5, ly - 3.5, lx + 3.5, ly + 3.5,
                          fill=self._color, outline="#04140c")
            c.create_text(w - pad_r - 2, 9, anchor="ne",
                          text=f"{data[-1]:.0f}{self._unit}",
                          fill=self._color, font=self._f_last)
            c.create_text(pad_l + 2, 9, anchor="nw",
                          text=f"min {lo:.0f}   max {hi:.0f}",
                          fill=T.TEXT_FAINT, font=self._f_minmax)
