#!/usr/bin/env python3
"""Neon FPS Booster - professional FPS optimization app for Roblox.

Run:   python main.py           GUI
       python main.py --bench   CLI micro-benchmark
       python main.py --version
"""
import os
import sys
import threading
import time
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import theme as T                                   # noqa: E402
from app.core import repo as repo_core                       # noqa: E402
from app.core import startup as startup_core                 # noqa: E402
from app.core.benchmark import RenderTest, performance_index, run_cpu_bench  # noqa: E402
from app.core.booster import IS_WIN, Booster                 # noqa: E402
from app.core.logstore import LogStore                       # noqa: E402
from app.core.settings_store import Settings                 # noqa: E402
from app.core.stats import SystemStats                       # noqa: E402
from app.i18n import detect, lang, set_lang, t               # noqa: E402
from app.ui import dashboard, logpage, optimizer, settings_page  # noqa: E402
from app.ui.frame import AppFrame                            # noqa: E402
from app.ui.logo import asset_logo_path, draw_logo, load_logo_image  # noqa: E402
from app.ui.widgets import NeonButton, StatBar, font         # noqa: E402


def _is_admin():
    if sys.platform == "win32":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    try:
        return os.geteuid() == 0
    except Exception:
        return False


class NeonApp:
    """Application orchestrator: sidebar, pages, workers, boost flow."""

    def __init__(self):
        self.settings = Settings()
        self.log = LogStore()
        self.stats = SystemStats()
        self.booster = Booster(self.settings, self.log)
        self.admin = _is_admin()
        self._busy = False
        self._stats_dirty = False
        self._idx_ema = None
        self._last_draw_fps = 0.0
        self._tick_n = 0
        self._render_test = None
        self.current_page = "dashboard"
        self.pages = {}

        stored = self.settings.get("lang", "auto")
        set_lang(detect() if stored == "auto" else stored)

        self.root = AppFrame(t("titlebar.app"), t("titlebar.tagline"), T.VERSION)
        self.root.withdraw()
        self.root._on_close = self.shutdown

        self._build_sidebar()
        self.content = tk.Frame(self.root.body, bg=T.BG0)
        self.content.pack(side="left", fill="both", expand=True)
        self._build_pages()

        self.log.subscribe(
            lambda e: self._safe_after(0, lambda e=e: self._log_gui(e)))

        threading.Thread(target=self._stats_loop, daemon=True).start()
        threading.Thread(target=self._autoprio_loop, daemon=True).start()
        self.root.after(200, self._tick)

        self.log.info(t("log.started"))
        if not self.admin and IS_WIN:
            self.log.info(t("log.admin_hint"))

    # ---------------- helpers ----------------
    def _safe_after(self, ms, fn):
        try:
            self.root.after(ms, fn)
        except Exception:
            pass

    def stats_refresh(self):
        self._stats_dirty = True

    # ---------------- sidebar ----------------
    def _build_sidebar(self):
        sb = tk.Frame(self.root.body, bg=T.BG1, width=T.SIDEBAR_W,
                      highlightbackground=T.BORDER, highlightthickness=1)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        top = tk.Frame(sb, bg=T.BG1)
        top.pack(fill="x", padx=18, pady=(20, 8))
        self.logo_c = tk.Canvas(top, width=52, height=52, bg=T.BG1,
                                highlightthickness=0)
        self.logo_c.pack(side="left")
        self._paint_logo()
        names = tk.Frame(top, bg=T.BG1)
        names.pack(side="left", padx=(12, 0))
        tk.Label(names, text="NEON FPS", bg=T.BG1, fg=T.TEXT,
                 font=font(15, True)).pack(anchor="w")
        tk.Label(names, text="BOOSTER", bg=T.BG1, fg=T.ACCENT,
                 font=font(15, True)).pack(anchor="w")

        self.nav_btns = {}
        icons = {"dashboard": "\u25c9", "optimizer": "\u26a1",
                 "settings": "\u2699", "log": "\u25a4"}
        for key in ("dashboard", "optimizer", "settings", "log"):
            self._nav_row(sb, key, icons[key])

        bottom = tk.Frame(sb, bg=T.BG1)
        bottom.pack(side="bottom", fill="x", padx=18, pady=14)
        st = tk.Frame(bottom, bg=T.BG1)
        st.pack(fill="x")
        self.game_dot_sb = tk.Label(st, text="\u25cf", bg=T.BG1,
                                    fg=T.TEXT_FAINT, font=font(8))
        self.game_dot_sb.pack(side="left")
        tk.Label(st, text="ROBLOX", bg=T.BG1, fg=T.TEXT_FAINT,
                 font=font(8, True)).pack(side="left", padx=(6, 0))
        cpu = tk.Frame(bottom, bg=T.BG1)
        cpu.pack(fill="x", pady=(8, 0))
        tk.Label(cpu, text="CPU", bg=T.BG1, fg=T.TEXT_FAINT,
                 font=font(8, True)).pack(side="left")
        self.sb_cpu_lbl = tk.Label(cpu, text="0%", bg=T.BG1, fg=T.TEXT_DIM,
                                   font=font(8, mono=True))
        self.sb_cpu_lbl.pack(side="right")
        self.sb_cpu = StatBar(cpu, w=100, h=6)
        self.sb_cpu.pack(side="right", padx=(8, 6))
        tk.Label(bottom, text=f"v{T.VERSION} \u00b7 {T.CODE_NAME}", bg=T.BG1,
                 fg=T.TEXT_FAINT, font=font(8, mono=True)).pack(
            anchor="w", pady=(10, 0))

    def _paint_logo(self):
        try:
            self.logo_c.delete("all")
            self._logo_img = None
            p = asset_logo_path()
            if p:
                self._logo_img = load_logo_image(p, 52)
            if self._logo_img is not None:
                self.logo_c.create_image(26, 26, image=self._logo_img)
            else:
                draw_logo(self.logo_c, 52)
        except Exception:
            try:
                draw_logo(self.logo_c, 52)
            except Exception:
                pass

    def _nav_row(self, parent, key, icon):
        row = tk.Frame(parent, bg=T.BG1, cursor="hand2")
        row.pack(fill="x", padx=10, pady=2)
        row._key = key
        bar = tk.Frame(row, bg=T.BG1, width=3)
        bar.pack(side="left", fill="y", pady=8)
        ic = tk.Label(row, text=icon, bg=T.BG1, fg=T.TEXT_DIM, font=font(11))
        ic.pack(side="left", padx=(12, 10), pady=9)
        tx = tk.Label(row, text=t(f"nav.{key}"), bg=T.BG1, fg=T.TEXT_DIM,
                      font=font(11, True))
        tx.pack(side="left", pady=9)
        for w in (row, ic, tx):
            w.bind("<Button-1>", lambda e, k=key: self.show_page(k))
            w.bind("<Enter>", lambda e, r=row: self._nav_paint(r, True))
            w.bind("<Leave>", lambda e, r=row: self._nav_paint(r, False))
        self.nav_btns[key] = {"row": row, "bar": bar, "icon": ic, "txt": tx}

    def _nav_paint(self, row, hover):
        key = getattr(row, "_key", None)
        if key not in self.nav_btns:
            return
        b = self.nav_btns[key]
        active = self.current_page == key
        bg = T.BG2 if (active or hover) else T.BG1
        fg = T.TEXT if (active or hover) else T.TEXT_DIM
        for w in (b["row"], b["icon"], b["txt"]):
            w.configure(bg=bg, fg=fg)
        b["bar"].configure(bg=T.ACCENT if active else T.BG1)

    # ---------------- pages ----------------
    def _build_pages(self):
        for child in self.content.winfo_children():
            child.destroy()
        self.pages = {}
        holder = tk.Frame(self.content, bg=T.BG0)
        holder.pack(fill="both", expand=True)
        self.pages["dashboard"] = dashboard.DashboardPage(holder, self)
        self.pages["optimizer"] = optimizer.OptimizerPage(holder, self)
        self.pages["settings"] = settings_page.SettingsPage(holder, self)
        self.pages["log"] = logpage.LogPage(holder, self)
        for p in self.pages.values():
            p.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.dashboard = self.pages["dashboard"]
        self.optimizer_page = self.pages["optimizer"]
        self.settings_page = self.pages["settings"]
        self.log_page = self.pages["log"]
        self.show_page(self.current_page)

    def show_page(self, key):
        if key not in self.pages:
            return
        self.current_page = key
        self.pages[key].tkraise()
        for k, b in self.nav_btns.items():
            self._nav_paint(b["row"], False)

    # ---------------- tick loop ----------------
    def _tick(self):
        self._tick_n += 1
        if self._stats_dirty:
            self._stats_dirty = False
            try:
                self.dashboard.update_stats(self.stats)
                self.sb_cpu.set(self.stats.cpu)
                self.sb_cpu_lbl.configure(text=f"{self.stats.cpu:.0f}%")
                self.game_dot_sb.configure(
                    fg=T.ACCENT if self.stats.game_pid else T.TEXT_FAINT)
            except Exception:
                pass
        if not self._busy and self._tick_n % 9 == 0:
            threading.Thread(target=self._sample_worker, daemon=True).start()
        self._safe_after(250, self._tick)

    def _stats_loop(self):
        while True:
            try:
                self.stats.refresh()
            except Exception:
                pass
            time.sleep(0.5)
            self._stats_dirty = True

    def _sample_worker(self):
        try:
            mopss = run_cpu_bench(0.15)
        except Exception:
            return
        self._safe_after(0, lambda: self._sample_done(mopss))

    def _sample_done(self, mopss):
        idx = performance_index(mopss, self._last_draw_fps)
        if self._idx_ema is None:
            self._idx_ema = idx
        else:
            self._idx_ema = int(0.7 * idx + 0.3 * self._idx_ema)
        self.dashboard.set_index(self._idx_ema)
        self.dashboard.push_chart(idx)

    # ---------------- benchmark ----------------
    def run_benchmark(self):
        if self._busy:
            return
        self._busy = True
        self.dashboard.set_bench_btn(True)
        self.log.info("benchmark started")
        threading.Thread(target=self._bench_worker, daemon=True).start()

    def _bench_worker(self):
        try:
            idx = self._bench_phase()
            self._safe_after(0, lambda: self._bench_done(idx))
        except Exception as e:
            self.log.error(f"benchmark failed: {e}")
            self._safe_after(0, self._bench_failed)

    def _bench_phase(self, cpu_dur=1.2, render_dur=1.4):
        mopss = run_cpu_bench(cpu_dur)
        fps = self._run_render(render_dur)
        self._last_draw_fps = fps
        return performance_index(mopss, fps)

    def _run_render(self, duration):
        result = {"fps": 0.0}
        done = threading.Event()

        def start():
            self._render_test = RenderTest(
                self.dashboard.chart, duration=duration,
                on_done=lambda fps: (result.update(fps=fps), done.set()))
            self._render_test.start()

        self._safe_after(0, start)
        done.wait(timeout=duration + 4.0)
        return result["fps"]

    def _bench_done(self, idx):
        self._busy = False
        self.dashboard.set_bench_btn(False)
        self._idx_ema = idx
        self.dashboard.set_index(idx)
        self.dashboard.push_chart(idx)
        best = self.settings.get("bench_best")
        if not best or idx > best:
            self.settings.set("bench_best", idx)
        self.dashboard.set_last_bench(f"{t('dash.last')}: {idx}")
        self.log.ok(f"benchmark: index {idx} (best {self.settings.get('bench_best')})")

    def _bench_failed(self):
        self._busy = False
        self.dashboard.set_bench_btn(False)

    # ---------------- boost ----------------
    def boost_now(self):
        if self._busy:
            return
        self._busy = True
        self.dashboard.set_boosting(True)
        self.log.info(t("log.boost.start"))
        threading.Thread(target=self._boost_worker, daemon=True).start()

    def _boost_worker(self):
        try:
            self._before = self._bench_phase(1.0, 1.2)
            enabled = [k for k, v in (self.settings.get("opt") or {}).items()
                       if v and k != "autoprio"]
            results = {}
            if enabled:
                results = self.booster.apply_all(
                    enabled,
                    on_step=lambda i, n, k: self._safe_after(
                        0, lambda i=i, n=n, k=k: self.dashboard.set_progress(i, n, k)))
            self._after = self._bench_phase(1.0, 1.2)
            self._safe_after(0, lambda: self._boost_done(results))
        except Exception as e:
            self.log.error(f"boost failed: {e}")
            self._safe_after(0, lambda: self._boost_done(None))

    def _boost_done(self, results):
        self._busy = False
        self.dashboard.set_boosting(False)
        self.optimizer_page.refresh()
        if results is None:
            return
        delta = self._after - self._before
        sign = "+" if delta >= 0 else ""
        head = [f"{t('modal.before')}: {self._before}   "
                f"{t('modal.delta')}: {sign}{delta}   "
                f"{t('modal.after')}: {self._after}"]
        lines = []
        for k, (ok, msg) in results.items():
            lines.append(f"{'+' if ok else '!'} {k}: {msg}")
        self.log.ok(f"boost complete: index {self._before} -> {self._after} ({sign}{delta})")
        self._modal(t("modal.boost"), head + lines)

    def apply_all_now(self):
        if self._busy:
            return
        self._busy = True
        threading.Thread(target=self._apply_worker, daemon=True).start()

    def _apply_worker(self):
        enabled = [k for k, v in (self.settings.get("opt") or {}).items()
                   if v and k != "autoprio"]
        try:
            self.booster.apply_all(enabled)
        except Exception as e:
            self.log.error(str(e))
        self._safe_after(0, self._apply_done)

    def _apply_done(self):
        self._busy = False
        self.optimizer_page.refresh()

    def restore_defaults(self):
        if self._busy:
            return
        self._busy = True
        threading.Thread(target=self._revert_worker, daemon=True).start()

    def _revert_worker(self):
        try:
            self.booster.revert_all()
        except Exception as e:
            self.log.error(str(e))
        self._safe_after(0, self._revert_done)

    def _revert_done(self):
        self._busy = False
        self.optimizer_page.refresh()
        self.log.info(t("log.reverted"))

    def priority_now(self):
        def worker():
            ok, msg = self.booster.apply("priority")
            self.log.info(f"priority: {msg}")
            self._safe_after(0, self.stats_refresh)
        threading.Thread(target=worker, daemon=True).start()

    # ---------------- auto game mode ----------------
    def _autoprio_loop(self):
        while True:
            time.sleep(2.0)
            try:
                if not self.settings.get("opt.autoprio", True):
                    continue
                prio = self.stats.game_priority
                if self.stats.game_pid and prio in (None, "Normal",
                                                    "Below Normal", "Idle",
                                                    "Above Normal"):
                    ok, _msg = self.stats.set_game_priority_high()
                    if ok:
                        self.log.ok(t("log.autoprio"))
            except Exception:
                pass

    # ---------------- repository update ----------------
    def fetch_latest(self, on_ok=None, on_fail=None):
        repo = self.settings.get("repo") or repo_core.DEFAULT_REPO
        branch = self.settings.get("branch") or "main"
        self.log.info(f"fetching {repo} ({branch})")

        def worker():
            try:
                appdir = repo_core.fetch_repo(
                    repo, branch, workdir=repo_core.cache_dir(), force=True)
                commit = repo_core.latest_commit(appdir)
                self.settings.set("last_update", time.time())
                self.log.ok(f"update downloaded: {repo}@{branch} {commit or ''}".rstrip())
                def done():
                    if on_ok:
                        on_ok()
                    self._modal(t("modal.updated"),
                                [f"{repo}  \u00b7  {branch}  \u00b7  {commit or 'tarball'}",
                                 t("modal.updated.hint")])
                self._safe_after(0, done)
            except Exception as e:
                self.log.error(f"fetch failed: {e}")
                self._safe_after(0, lambda: on_fail() if on_fail else None)

        threading.Thread(target=worker, daemon=True).start()

    # ---------------- language / reset / startup ----------------
    def set_lang(self, code):
        self.settings.set("lang", code)
        set_lang(code)
        self._rebuild_ui_text()
        self.log.info(f"language: {code}")

    def _rebuild_ui_text(self):
        tb = self.root.titlebar
        tb.title_lbl.configure(text=t("titlebar.app"))
        tb.sub_lbl.configure(text=t("titlebar.tagline"))
        for key, b in self.nav_btns.items():
            b["txt"].configure(text=t(f"nav.{key}"))
        self._build_pages()

    def factory_reset(self):
        self.settings.reset()
        stored = self.settings.get("lang", "auto")
        set_lang(detect() if stored == "auto" else stored)
        self._rebuild_ui_text()
        self.log.info(t("set.reset.done"))

    def set_startup(self, enabled):
        try:
            return startup_core.set_enabled(bool(enabled))
        except Exception:
            return False

    # ---------------- modals / log ----------------
    def _modal(self, title, lines, title_color=T.ACCENT):
        win = tk.Toplevel(self.root)
        win.configure(bg=T.BG0)
        win.overrideredirect(True)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        w, h = 480, 120 + 22 * len(lines)
        x = self.root.winfo_x() + max(0, (self.root.winfo_width() - w) // 2)
        y = self.root.winfo_y() + max(0, (self.root.winfo_height() - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        inner = tk.Frame(win, bg=T.BG1, highlightbackground=T.BORDER_HI,
                         highlightthickness=1)
        inner.place(x=1, y=1, width=w - 2, height=h - 2)
        cv = tk.Canvas(inner, width=84, height=84, bg=T.BG1,
                       highlightthickness=0)
        cv.place(x=16, y=18)
        draw_logo(cv, 84)
        tk.Label(inner, text=title, bg=T.BG1, fg=title_color,
                 font=font(16, True)).place(x=118, y=26)
        ly = 64
        for line in lines[:6]:
            tk.Label(inner, text=line, bg=T.BG1, fg=T.TEXT_DIM,
                     font=font(10, mono=True), anchor="w").place(
                x=118, y=ly, anchor="nw")
            ly += 22
        btn = NeonButton(inner, t("modal.ok"), style="primary",
                         size=11, padx=26, pady=8)
        btn.place(x=w - 100, y=h - 52)

        def ok():
            try:
                win.destroy()
            except Exception:
                pass
        btn._command = ok
        try:
            win.lift()
            win.focus_force()
        except Exception:
            pass
        return win

    def _log_gui(self, entry):
        page = self.pages.get("log")
        if page:
            page.add_entry(entry)

    # ---------------- shutdown ----------------
    def shutdown(self):
        try:
            if self._render_test:
                self._render_test.cancel()
        except Exception:
            pass


def show_splash(app):
    """Short boot splash, then reveal the main window."""
    root = app.root
    sp = tk.Toplevel(root)
    sp.overrideredirect(True)
    sp.configure(bg=T.BG0)
    w, h = 500, 330
    x = root.winfo_rootx() + max(0, (root.winfo_width() - w) // 2)
    y = root.winfo_rooty() + max(0, (root.winfo_height() - h) // 2)
    sp.geometry(f"{w}x{h}+{x}+{y}")
    try:
        sp.attributes("-topmost", True)
    except Exception:
        pass
    inner = tk.Frame(sp, bg=T.BG1, highlightbackground=T.BORDER_HI,
                     highlightthickness=1)
    inner.place(x=1, y=1, width=w - 2, height=h - 2)

    logo_c = tk.Canvas(inner, width=110, height=110, bg=T.BG1,
                       highlightthickness=0)
    logo_c.place(x=(w - 2) // 2 - 55, y=44)
    img = None
    p = asset_logo_path()
    if p:
        img = load_logo_image(p, 110)
    if img is not None:
        logo_c.create_image(55, 55, image=img)
    else:
        draw_logo(logo_c, 110)

    tk.Label(inner, text=T.PRODUCT, bg=T.BG1, fg=T.TEXT,
             font=font(20, True)).place(x=(w - 2) // 2, y=170, anchor="n")
    tk.Label(inner, text=T.CODE_NAME, bg=T.BG1, fg=T.ACCENT,
             font=font(11, True)).place(x=(w - 2) // 2, y=198, anchor="n")

    bar_x1, bar_x2, bar_y1, bar_y2 = 150, w - 150, 250, 258
    cv = tk.Canvas(inner, width=w - 2, height=h - 2, bg=T.BG1,
                   highlightthickness=0)
    cv.place(x=0, y=240)
    cv.create_rectangle(bar_x1, 10, bar_x2, 18, fill=T.BG3, outline="")
    fg = cv.create_rectangle(bar_x1, 10, bar_x1, 18, fill=T.ACCENT, outline="")
    tk.Label(inner, text=f"v{T.VERSION}  \u00b7  github.com/Ven1x-cloud/simple-fps-booster",
             bg=T.BG1, fg=T.TEXT_FAINT, font=font(8, mono=True)).place(
        x=(w - 2) // 2, y=286, anchor="n")

    steps = 8

    def step(i=0):
        if i < steps:
            try:
                cv.coords(fg, bar_x1, 10,
                          bar_x1 + (bar_x2 - bar_x1) * (i + 1) / steps, 18)
            except Exception:
                pass
            sp.after(110, lambda: step(i + 1))
        else:
            def go():
                try:
                    sp.destroy()
                except Exception:
                    pass
                root.deiconify()
                root.lift()
                try:
                    root.focus_force()
                except Exception:
                    pass
            sp.after(180, go)

    sp.after(120, step)


def main():
    app = NeonApp()
    show_splash(app)
    app.root.mainloop()
    return app


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--bench":
        _mopss = run_cpu_bench(2.0)
        print(f"CPU micro-benchmark: {_mopss:.1f} MOp/s")
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(T.VERSION)
        sys.exit(0)
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
