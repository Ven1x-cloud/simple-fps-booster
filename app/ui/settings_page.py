"""Settings page: repository, language, general, background apps."""
import datetime
import tkinter as tk

from .. import theme as T
from ..i18n import lang, t
from .widgets import Card, CardTitle, NeonButton, Toggle, font


class SettingsPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=T.BG0)
        self.app = app
        self.check_vars = {}

        wrap = tk.Frame(self, bg=T.BG0)
        wrap.pack(fill="both", expand=True, padx=22, pady=(16, 16))
        wrap.columnconfigure(0, weight=5, uniform="s")
        wrap.columnconfigure(1, weight=5, uniform="s")
        wrap.rowconfigure(0, weight=1)
        wrap.rowconfigure(1, weight=1)

        # ---------------- repository ----------------
        self.card_repo = Card(wrap)
        self.card_repo.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        rb = self.card_repo.body
        CardTitle(rb, t("set.repo")).pack(anchor="w", pady=(0, 6))
        tk.Label(rb, text=t("set.repo.hint"), bg=T.BG1, fg=T.TEXT_DIM,
                 font=font(9), justify="left").pack(anchor="w", pady=(0, 10))

        def entry(parent, width=30):
            return tk.Entry(parent, width=width, bg=T.BG2, fg=T.TEXT,
                            insertbackground=T.ACCENT, relief="flat",
                            font=font(10, mono=True), highlightthickness=1,
                            highlightbackground=T.BORDER,
                            highlightcolor=T.ACCENT_DIM)

        tk.Label(rb, text=t("set.repo.name"), bg=T.BG1, fg=T.TEXT_DIM,
                 font=font(9, True)).pack(anchor="w")
        self.repo_ent = entry(rb)
        self.repo_ent.pack(fill="x", pady=(2, 8))
        tk.Label(rb, text=t("set.repo.branch"), bg=T.BG1, fg=T.TEXT_DIM,
                 font=font(9, True)).pack(anchor="w")
        self.branch_ent = entry(rb, width=18)
        self.branch_ent.pack(anchor="w", pady=(2, 12))

        fetch_row = tk.Frame(rb, bg=T.BG1)
        fetch_row.pack(anchor="w")
        self.fetch_btn = NeonButton(fetch_row, t("set.repo.fetch"),
                                    command=self._fetch, style="accent",
                                    size=10, padx=14, pady=6)
        self.fetch_btn.pack(side="left")
        self.fetch_status = tk.Label(fetch_row, text="", bg=T.BG1,
                                     fg=T.TEXT_DIM, font=font(9, mono=True))
        self.fetch_status.pack(side="left", padx=(10, 0))

        last = self.app.settings.get("last_update")
        if last:
            stamp = datetime.datetime.fromtimestamp(last).strftime("%Y-%m-%d %H:%M")
            tk.Label(rb, text=f"last update: {stamp}", bg=T.BG1,
                     fg=T.TEXT_FAINT, font=font(9, mono=True)).pack(
                anchor="w", pady=(8, 0))

        # ---------------- language ----------------
        self.card_lang = Card(wrap)
        self.card_lang.grid(row=0, column=1, sticky="nsew")
        lb = self.card_lang.body
        CardTitle(lb, t("set.lang")).pack(anchor="w", pady=(0, 10))
        self.lang_btns = {}
        for code, key in (("en", "set.lang.en"), ("nl", "set.lang.nl")):
            b = NeonButton(lb, t(key), style="ghost", size=11, padx=18)
            b._command = lambda c=code: app.set_lang(c)
            b.pack(anchor="w", pady=3, padx=4)
            self.lang_btns[code] = b
        self._sync_lang()

        # ---------------- general ----------------
        self.card_gen = Card(wrap)
        self.card_gen.grid(row=1, column=0, sticky="nsew", padx=(0, 10),
                           pady=(10, 0))
        gb = self.card_gen.body
        CardTitle(gb, t("set.general")).pack(anchor="w", pady=(0, 8))

        r1 = tk.Frame(gb, bg=T.BG1)
        r1.pack(fill="x")
        tk.Label(r1, text=t("set.startup"), bg=T.BG1, fg=T.TEXT,
                 font=font(11, True)).pack(side="left")
        self.startup_tg = Toggle(
            r1, value=bool(self.app.settings.get("startup", False)),
            command=self._startup)
        self.startup_tg.pack(side="right")

        r2 = tk.Frame(gb, bg=T.BG1)
        r2.pack(fill="x", pady=(8, 0))
        tk.Label(r2, text=t("opt.items.autoprio"), bg=T.BG1, fg=T.TEXT,
                 font=font(11, True)).pack(side="left")
        self.autoprio_tg = Toggle(
            r2, value=bool(self.app.settings.get("opt.autoprio", True)),
            command=self._autoprio)
        self.autoprio_tg.pack(side="right")

        self.reset_btn = NeonButton(gb, t("set.reset"), command=self._reset,
                                    style="danger", size=10, padx=14, pady=6)
        self.reset_btn.pack(anchor="w", pady=(16, 0))

        # ---------------- background apps ----------------
        self.card_apps = Card(wrap)
        self.card_apps.grid(row=1, column=1, sticky="nsew", pady=(10, 0))
        ab = self.card_apps.body
        CardTitle(ab, t("set.apps")).pack(anchor="w", pady=(0, 4))
        tk.Label(ab, text=t("set.apps.hint"), bg=T.BG1, fg=T.TEXT_DIM,
                 font=font(9), justify="left").pack(anchor="w", pady=(0, 8))

        self.apps_box = tk.Frame(ab, bg=T.BG2, highlightbackground=T.BORDER,
                                 highlightthickness=1)
        self.apps_box.pack(fill="both", expand=True)
        for name in self.app.settings.get("kill_list", []):
            self._add_check(name)

        add_row = tk.Frame(ab, bg=T.BG1)
        add_row.pack(fill="x", pady=(10, 0))
        self.add_ent = tk.Entry(add_row, width=24, bg=T.BG2, fg=T.TEXT,
                                insertbackground=T.ACCENT, relief="flat",
                                font=font(10, mono=True), highlightthickness=1,
                                highlightbackground=T.BORDER,
                                highlightcolor=T.ACCENT_DIM)
        self.add_ent.pack(side="left")
        self.add_ent.bind("<Return>", lambda e: self._add_app())
        NeonButton(add_row, "+", command=self._add_app, style="accent",
                   size=11, padx=14, pady=6).pack(side="left", padx=(8, 0))

    # ---------- app list ----------
    def _add_check(self, name):
        if name in self.check_vars:
            return
        row = tk.Frame(self.apps_box, bg=T.BG2)
        row.pack(fill="x", padx=8, pady=3)
        var = tk.BooleanVar(value=True)
        self.check_vars[name] = var
        tk.Checkbutton(row, text=name, variable=var, bg=T.BG2, fg=T.TEXT_DIM,
                       activebackground=T.BG2, activeforeground=T.TEXT,
                       selectcolor=T.BG3, font=font(10, mono=True),
                       cursor="hand2", anchor="w").pack(
            side="left", fill="x", expand=True)

    def _add_app(self):
        name = self.add_ent.get().strip()
        if not name:
            return
        if not name.lower().endswith(".exe"):
            name += ".exe"
        self._add_check(name)
        self._save_kill_list()
        self.add_ent.delete(0, "end")

    def _save_kill_list(self):
        self.app.settings.set("kill_list", list(self.check_vars.keys()))

    # ---------- actions ----------
    def _fetch(self):
        repo = self.repo_ent.get().strip()
        branch = self.branch_ent.get().strip()
        if not repo:
            return
        self.app.settings.set("repo", repo)
        self.app.settings.set("branch", branch or "main")
        self.fetch_btn.set_enabled(False)
        self.fetch_btn.set_text(t("set.repo.fetching"))
        self.fetch_status.configure(text="")
        self.app.fetch_latest(on_ok=lambda: self._fetch_done(True),
                              on_fail=lambda: self._fetch_done(False))

    def _fetch_done(self, ok):
        self.fetch_btn.set_enabled(True)
        self.fetch_btn.set_text(t("set.repo.fetch"))
        self.fetch_status.configure(
            text=t("set.repo.ok") if ok else t("set.repo.fail"),
            fg=T.ACCENT if ok else T.DANGER)

    def _startup(self, v):
        ok = self.app.set_startup(bool(v))
        if not ok:
            v = not v
        self.app.settings.set("startup", v)
        self.startup_tg.set(bool(v), fire=False)

    def _autoprio(self, v):
        self.app.settings.set("opt.autoprio", bool(v))

    def _reset(self):
        self.app.factory_reset()

    def _sync_lang(self):
        cur = lang()
        for code, b in self.lang_btns.items():
            style = "primary" if code == cur else "ghost"
            b._style = b.STYLES[style]
            b._draw()

    def refresh(self):
        self.repo_ent.delete(0, "end")
        self.repo_ent.insert(0, self.app.settings.get("repo", ""))
        self.branch_ent.delete(0, "end")
        self.branch_ent.insert(0, self.app.settings.get("branch", ""))
        self.startup_tg.set(bool(self.app.settings.get("startup", False)),
                            fire=False)
        self.autoprio_tg.set(bool(self.app.settings.get("opt.autoprio", True)),
                             fire=False)
        self._sync_lang()
        for child in self.apps_box.winfo_children():
            child.destroy()
        self.check_vars.clear()
        for name in self.app.settings.get("kill_list", []):
            self._add_check(name)
