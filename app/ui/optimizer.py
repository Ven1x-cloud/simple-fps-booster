"""Optimizer page: toggles per optimization + apply all / restore defaults."""
import tkinter as tk

from .. import theme as T
from ..i18n import t
from .widgets import Card, CardTitle, NeonButton, Toggle, font

SECTIONS = [
    ("game", ("priority", "autoprio")),
    ("win", ("gamedvr", "gamebar", "notifications", "power")),
    ("adv", ("services", "killapps")),
]


class OptimizerPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=T.BG0)
        self.app = app
        self.rows = {}

        top = tk.Frame(self, bg=T.BG0)
        top.pack(fill="x", padx=22, pady=(16, 8))
        tk.Label(top, text=t("opt.title"), bg=T.BG0, fg=T.TEXT_FAINT,
                 font=font(10, True)).pack(side="left")
        self.revert_btn = NeonButton(top, t("opt.revert"),
                                     command=app.restore_defaults,
                                     style="danger", size=10, padx=14, pady=5)
        self.revert_btn.pack(side="right")
        self.apply_btn = NeonButton(top, t("opt.apply"),
                                    command=app.apply_all_now,
                                    style="primary", size=10, padx=14, pady=5)
        self.apply_btn.pack(side="right", padx=(0, 8))

        if not app.admin:
            tk.Label(self, text=t("opt.admin.hint"), bg=T.BG0, fg=T.WARN,
                     font=font(9)).pack(anchor="w", padx=24)

        wrap = tk.Frame(self, bg=T.BG0)
        wrap.pack(fill="both", expand=True, padx=22, pady=(0, 16))

        for sec_key, items in SECTIONS:
            sec = Card(wrap)
            sec.pack(fill="x", pady=(0, 10))
            b = sec.body
            CardTitle(b, t(f"opt.sec.{sec_key}")).pack(anchor="w", pady=(0, 8))
            for item_id in items:
                self._item_row(b, item_id)

    def _item_row(self, parent, item_id):
        row = tk.Frame(parent, bg=T.BG1, cursor="hand2")
        row.pack(fill="x", pady=3, ipady=7, padx=4,
                 highlightbackground=T.BORDER, highlightthickness=1)

        val = bool(self.app.settings.get(f"opt.{item_id}", False))
        tg = Toggle(row, value=val, command=lambda v, k=item_id: self._toggle(k, v))
        tg.pack(side="left", padx=(10, 12))

        badge = tk.Label(row, text="", bg=T.BG2, fg=T.TEXT_FAINT,
                         font=font(9, True, mono=True), padx=10, pady=4,
                         highlightbackground=T.BORDER, highlightthickness=1)
        badge.pack(side="right", padx=10)

        names = tk.Frame(row, bg=T.BG1)
        names.pack(side="left", fill="x", expand=True)
        tk.Label(names, text=t(f"opt.items.{item_id}"), bg=T.BG1, fg=T.TEXT,
                 font=font(11, True)).pack(anchor="w")
        tk.Label(names, text=t(f"opt.desc.{item_id}"), bg=T.BG1, fg=T.TEXT_DIM,
                 font=font(9)).pack(anchor="w")
        self.rows[item_id] = {"toggle": tg, "badge": badge}
        self._refresh_badge(item_id)
        # row click mirrors the toggle (ignoring clicks on the toggle itself)
        row.bind("<Button-1>",
                 lambda e, k=item_id, tg=tg: self._row_click(k, tg, e))

    def _row_click(self, item_id, tg, e):
        if e.widget is tg:
            return
        self._toggle(item_id, not tg.get())

    def _toggle(self, item_id, value):
        self.app.settings.set(f"opt.{item_id}", bool(value))
        self.rows[item_id]["toggle"].set(bool(value), fire=False)
        self._refresh_badge(item_id)
        self.app.log.info(f"toggle {item_id} -> {int(bool(value))}")

    def _refresh_badge(self, item_id):
        r = self.rows.get(item_id)
        if not r:
            return
        applied = self.app.booster.applied_ids()
        on = bool(self.app.settings.get(f"opt.{item_id}", False))
        if item_id in applied:
            text, fg, bg = t("opt.applied"), T.ACCENT, T.ACCENT_BG
        elif on:
            text, fg, bg = t("opt.on"), T.TEXT_DIM, T.BG2
        else:
            text, fg, bg = t("opt.off"), T.TEXT_FAINT, T.BG2
        r["badge"].configure(text=text, fg=fg, bg=bg)

    def refresh(self):
        for item_id in self.rows:
            self.rows[item_id]["toggle"].set(
                bool(self.app.settings.get(f"opt.{item_id}", False)), fire=False)
            self._refresh_badge(item_id)
