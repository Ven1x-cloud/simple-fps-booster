"""Frameless main window with a custom neon title bar.

On Windows the caption is removed with Win32 style flags (taskbar entry is
kept). Fallback: overrideredirect(True).
"""
import platform
import tkinter as tk

from .. import theme as T
from .logo import draw_logo, asset_logo_path, load_logo_image
from .widgets import font

try:
    import ctypes
except Exception:  # pragma: no cover
    ctypes = None


class Titlebar(tk.Frame):
    def __init__(self, app, title, subtitle, version):
        super().__init__(app, bg=T.BG0, height=T.TITLEBAR_H)
        self.app = app
        self._drag = {"x": 0, "y": 0}
        self.pack(side="top", fill="x")
        self.pack_propagate(False)

        # --- left: logo + title + version chip ---
        self.logo_c = tk.Canvas(self, width=30, height=30, bg=T.BG0,
                                highlightthickness=0)
        self.logo_c.pack(side="left", padx=(14, 10), pady=8)
        self._img_ref = None
        img = None
        p = asset_logo_path()
        if p:
            img = load_logo_image(p, 30)
        if img is not None:
            self._img_ref = img
            self.logo_c.create_image(15, 15, image=img)
        else:
            draw_logo(self.logo_c, 30)

        self.title_lbl = tk.Label(self, text=title, bg=T.BG0, fg=T.TEXT,
                                  font=font(13, True))
        self.title_lbl.pack(side="left")
        self.sub_lbl = tk.Label(self, text=subtitle, bg=T.BG0, fg=T.TEXT_DIM,
                                font=font(9))
        self.sub_lbl.pack(side="left", padx=(8, 0))
        chip = tk.Label(self, text=f"v{version}", bg=T.ACCENT_BG, fg=T.ACCENT,
                        font=font(9, True, mono=True), padx=8, pady=2,
                        highlightbackground=T.ACCENT_DIM, highlightthickness=1)
        chip.pack(side="left", padx=10)
        self.chip = chip

        # --- right: window buttons (close, maximize, minimize) ---
        self._buttons = {}
        for key, glyph, cmd, hover in (("close", "\u2715", app.close_win,
                                        T.DANGER_HOVER),
                                       ("max", "\u25a2", app.toggle_max, T.BG3),
                                       ("min", "\u2013", app.minimize, T.BG3)):
            b = tk.Label(self, text=glyph, bg=T.BG0, fg=T.TEXT_DIM,
                         font=font(11, True), cursor="hand2", padx=10)
            b.pack(side="right", fill="y")
            self._buttons[key] = b
            b.bind("<Enter>", lambda e, b=b, h=hover:
                   b.configure(bg=h, fg=T.TEXT))
            b.bind("<Leave>", lambda e, b=b:
                   b.configure(bg=T.BG0, fg=T.TEXT_DIM))
            b.bind("<Button-1>", lambda e, c=cmd: c())
        tk.Label(self, text="", bg=T.BG0, width=8).pack(side="right")

        # --- dragging ---
        for w in (self, self.title_lbl, self.sub_lbl):
            self._bind_drag(w)

    def _bind_drag(self, w):
        w.bind("<Button-1>", self._drag_start, add="+")
        w.bind("<B1-Motion>", self._drag_move, add="+")
        w.bind("<Double-Button-1>", lambda e: self.app.toggle_max(), add="+")

    def _drag_start(self, e):
        self._drag = {"x": e.x_root - self.app.winfo_x(),
                      "y": e.y_root - self.app.winfo_y()}

    def _drag_move(self, e):
        if self.app._maximized:
            return
        x = max(-80, e.x_root - self._drag["x"])
        y = max(0, e.y_root - self._drag["y"])
        self.app.geometry(f"+{x}+{y}")


class AppFrame(tk.Tk):
    """Main window: custom title bar + body area."""

    def __init__(self, title, subtitle, version, w=T.WINDOW_W, h=T.WINDOW_H):
        super().__init__()
        self.title(title)
        self.configure(bg=T.BG0)
        self._maximized = False
        self._saved_geom = None
        self._borderless = False
        self._on_close = None
        self.geometry(f"{w}x{h}")
        self._center(w, h)
        self._dpi_aware()
        self.titlebar = Titlebar(self, title, subtitle, version)
        self.body = tk.Frame(self, bg=T.BG0)
        self.body.pack(fill="both", expand=True)
        self.after(150, self._make_borderless)

    def _center(self, w, h):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(16, (sh - h) // 2 - 24)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _dpi_aware(self):
        if platform.system() != "Windows" or ctypes is None:
            return
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    def _make_borderless(self):
        if self._borderless:
            return
        if platform.system() == "Windows" and ctypes is not None:
            try:
                hwnd = self.winfo_id()
                GWL_STYLE, GWL_EXSTYLE = -16, -20
                WS_CAPTION, WS_THICKFRAME, WS_BORDER = 0x00C00000, 0x00040000, 0x00800000
                WS_EX_DLGMODALFRAME = 0x00000001
                WS_EX_CLIENTEDGE = 0x00000200
                WS_EX_WINDOWEDGE = 0x00000100
                user32 = ctypes.windll.user32
                cur = self.geometry()
                style = user32.GetWindowLongW(hwnd, GWL_STYLE)
                user32.SetWindowLongW(
                    hwnd, GWL_STYLE,
                    style & ~(WS_CAPTION | WS_THICKFRAME | WS_BORDER))
                ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                user32.SetWindowLongW(
                    hwnd, GWL_EXSTYLE,
                    ex & ~(WS_EX_DLGMODALFRAME | WS_EX_CLIENTEDGE | WS_EX_WINDOWEDGE))
                SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_FRAMECHANGED = (
                    0x0001, 0x0002, 0x0004, 0x0020)
                user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                    SWP_NOSIZE | SWP_NOMOVE |
                                    SWP_NOZORDER | SWP_FRAMECHANGED)
                self._borderless = True
                self.after(60, lambda: self.geometry(cur))
                return
            except Exception:
                pass
        try:
            self.overrideredirect(True)
        except Exception:
            pass
        self._borderless = True

    # ---------- window commands ----------
    def minimize(self):
        try:
            self.iconify()
        except Exception:
            pass

    def toggle_max(self):
        if not self._maximized:
            self._saved_geom = self.geometry()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f"{sw}x{sh}+0+0")
            self._maximized = True
        else:
            if self._saved_geom:
                try:
                    self.geometry(self._saved_geom)
                except Exception:
                    pass
            self._maximized = False

    def ensure_visible(self):
        """Force the (borderless) window to be shown/raised after deiconify.

        Windows can keep a caption-less window hidden after deiconify;
        ShowWindow + a topmost toggle is the reliable fix.
        """
        if platform.system() == "Windows" and ctypes is not None:
            try:
                ctypes.windll.user32.ShowWindow(self.winfo_id(), 5)  # SW_SHOW
            except Exception:
                pass
        try:
            self.attributes("-topmost", True)
            self.attributes("-topmost", False)
            self.lift()
        except Exception:
            pass

    def close_win(self):
        try:
            if self._on_close:
                self._on_close()
        finally:
            self.destroy()
