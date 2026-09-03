"""Activity log page."""
import datetime
import os
import tkinter as tk
from tkinter import filedialog

from .. import theme as T
from ..i18n import t
from .widgets import Card, NeonButton, font

COLORS = {
    "info": T.TEXT_DIM,
    "ok": T.ACCENT,
    "warn": T.WARN,
    "error": T.DANGER,
}


class LogPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=T.BG0)
        self.app = app

        top = tk.Frame(self, bg=T.BG0)
        top.pack(fill="x", padx=22, pady=(16, 8))
        tk.Label(top, text=t("log.title"), bg=T.BG0, fg=T.TEXT_FAINT,
                 font=font(10, True)).pack(side="left")
        NeonButton(top, t("log.save"), command=self.save, style="ghost",
                   size=10, padx=14, pady=5).pack(side="right")
        NeonButton(top, t("log.clear"), command=self.clear, style="ghost",
                   size=10, padx=14, pady=5).pack(side="right", padx=(0, 8))

        card = Card(self)
        card.pack(fill="both", expand=True, padx=22, pady=(0, 16))
        self.card = card

        self.text = tk.Text(card.body, bg=T.BG1, fg=T.TEXT, relief="flat",
                            font=font(10, mono=True), insertbackground=T.ACCENT,
                            state="disabled", wrap="none", highlightthickness=0,
                            spacing1=1, spacing3=1)
        sb = tk.Scrollbar(card.body, command=self.text.yview, bg=T.BG1,
                          troughcolor=T.BG0, activebackground=T.ACCENT_DIM,
                          highlightthickness=0, bd=0, width=12)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)

        for level, color in COLORS.items():
            self.text.tag_configure(level, foreground=color)

        # seed with existing entries
        for e in app.log.entries():
            self._append(e, autoscroll=False)

    def _stamp(self, ts):
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")

    def _append(self, entry, autoscroll=True):
        try:
            self.text.configure(state="normal")
            level = entry["level"] if entry["level"] in COLORS else "info"
            self.text.insert("end", f"{self._stamp(entry['ts'])}  ", "ts")
            self.text.insert("end", f"{level.upper():5}  ", level)
            self.text.insert("end", f"{entry['msg']}\n", level)
            if autoscroll:
                self.text.see("end")
            self.text.configure(state="disabled")
        except Exception:
            pass

    def add_entry(self, entry):
        self._append(entry)

    def clear(self):
        self.app.log.clear()
        try:
            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            self.text.configure(state="disabled")
        except Exception:
            pass

    def save(self):
        default_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        try:
            path = filedialog.asksaveasfilename(
                parent=self.app.root, defaultextension=".log",
                initialdir=default_dir, initialfile="neon-fps-booster.log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt")])
        except Exception:
            return
        if not path:
            return
        try:
            self.app.log.save(path)
            self.app.log.info(t("log.saved"))
        except Exception as e:
            self.app.log.error(f"save failed: {e}")
