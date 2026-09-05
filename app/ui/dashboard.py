"""Dashboard page: stats cards, gauge, boost control, game process, history."""
import tkinter as tk

from .. import theme as T
from ..i18n import t
from .widgets import (Card, CardTitle, Gauge, LineChart, NeonButton, StatBar,
                      font)


class DashboardPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=T.BG0)
        self.app = app

        tk.Label(self, text=t("dash.status"), bg=T.BG0, fg=T.TEXT_FAINT,
                 font=font(10, True)).pack(anchor="w", padx=22, pady=(16, 6))

        # ---------------- stat cards row ----------------
        row = tk.Frame(self, bg=T.BG0)
        row.pack(fill="x", padx=22, pady=(0, 10))
        for i in range(4):
            row.columnconfigure(i, weight=1, uniform="stats")
        row.rowconfigure(0, weight=1)

        self.card_fps = Card(row)
        self.card_fps.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.card_cpu = Card(row)
        self.card_cpu.grid(row=0, column=1, sticky="nsew", padx=(0, 8))
        self.card_ram = Card(row)
        self.card_ram.grid(row=0, column=2, sticky="nsew", padx=(0, 8))
        self.card_gpu = Card(row)
        self.card_gpu.grid(row=0, column=3, sticky="nsew")

        # FPS index card
        b = self.card_fps.body
        CardTitle(b, t("dash.fps")).pack(anchor="w")
        self.gauge = Gauge(b, size=150, max_value=1000, label=t("dash.fps"))
        self.gauge.pack(pady=(4, 0))
        tk.Label(b, text=t("dash.fps.sub"), bg=T.BG1, fg=T.TEXT_FAINT,
                 font=font(8)).pack(anchor="w")
        self.last_bench_lbl = tk.Label(b, text="", bg=T.BG1, fg=T.TEXT_DIM,
                                       font=font(9, mono=True))
        self.last_bench_lbl.pack(anchor="w", pady=(2, 0))

        # CPU / RAM / GPU cards
        self.cpu_lbl, self.cpu_bar = self._meter_card(self.card_cpu, "dash.cpu")
        self.ram_lbl, self.ram_bar = self._meter_card(self.card_ram, "dash.ram")
        self.gpu_lbl, self.gpu_bar = self._meter_card(self.card_gpu, "dash.gpu")

        # ---------------- main row ----------------
        row2 = tk.Frame(self, bg=T.BG0)
        row2.pack(fill="both", expand=True, padx=22, pady=(0, 16))
        row2.columnconfigure(0, weight=5, uniform="m")
        row2.columnconfigure(1, weight=4, uniform="m")
        row2.columnconfigure(2, weight=6, uniform="m")
        row2.rowconfigure(0, weight=1)

        # --- boost card ---
        self.card_boost = Card(row2, accent=T.ACCENT)
        self.card_boost.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        bb = self.card_boost.body
        mid = tk.Frame(bb, bg=T.BG1)
        mid.place(relx=0.5, rely=0.5, anchor="center")
        self.boost_btn = NeonButton(mid, t("dash.boost"), command=app.boost_now,
                                    style="primary", size=16, padx=34, pady=16,
                                    radius=12)
        self.boost_btn.pack()
        self.boost_sub = tk.Label(mid, text=t("dash.boost.sub"), bg=T.BG1,
                                  fg=T.TEXT_DIM, font=font(10))
        self.boost_sub.pack(pady=(10, 0))
        self.bench_btn = NeonButton(mid, t("dash.bench"),
                                    command=app.run_benchmark,
                                    style="accent", size=11)
        self.bench_btn.pack(pady=(22, 0))
        self.progress = StatBar(mid, w=230, h=6, color=T.ACCENT)
        self.progress.pack(pady=(18, 4))
        self.status_lbl = tk.Label(mid, text="", bg=T.BG1, fg=T.TEXT_FAINT,
                                   font=font(9, mono=True))
        self.status_lbl.pack()

        # --- game process card ---
        self.card_game = Card(row2)
        self.card_game.grid(row=0, column=1, sticky="nsew", padx=(0, 8))
        gb = self.card_game.body
        CardTitle(gb, t("dash.game")).pack(anchor="w", pady=(0, 8))
        self.game_dot = tk.Label(gb, text="\u25cf", bg=T.BG1, fg=T.TEXT_FAINT,
                                 font=font(9))
        self.game_dot.pack(anchor="w")
        self.game_state = tk.Label(gb, text=t("dash.game.idle"), bg=T.BG1,
                                   fg=T.TEXT_DIM, font=font(12, True))
        self.game_state.pack(anchor="w")
        self.game_rows = tk.Frame(gb, bg=T.BG1)
        self.game_rows.pack(anchor="w", pady=(10, 0), fill="x")
        self.game_name_lbl = self._game_row(gb, t("dash.game.name"))
        self.game_pid_lbl = self._game_row(gb, t("dash.game.pid"))
        self.game_cpu_lbl = self._game_row(gb, t("dash.game.cpu"))
        self.game_prio_lbl = self._game_row(gb, t("dash.game.prio"))
        self.game_prio_btn = NeonButton(gb, t("dash.game.apply"),
                                        command=app.priority_now,
                                        style="accent", size=10, padx=14, pady=6)
        self.game_prio_btn.pack(pady=(14, 0))

        # --- history chart card ---
        self.card_hist = Card(row2)
        self.card_hist.grid(row=0, column=2, sticky="nsew")
        hb = self.card_hist.body
        CardTitle(hb, t("dash.history")).pack(anchor="w")
        tk.Label(hb, text=t("dash.history.sub"), bg=T.BG1, fg=T.TEXT_FAINT,
                 font=font(8)).pack(anchor="w", pady=(0, 4))
        self.chart = LineChart(hb, w=430, h=220, samples=90)
        self.chart.pack(fill="both", expand=True)
        self.card_hist.bind("<Configure>", lambda e: self._chart_resize(e))

    # ---------- helpers ----------
    def _meter_card(self, card, key):
        b = card.body
        CardTitle(b, t(key)).pack(anchor="w")
        lbl = tk.Label(b, text="--", bg=T.BG1, fg=T.TEXT, font=font(24, True, mono=True))
        lbl.pack(pady=(6, 4))
        bar = StatBar(b, w=150, h=8)
        bar.pack(anchor="w")
        tk.Label(b, text=t("dash.load"), bg=T.BG1, fg=T.TEXT_FAINT,
                 font=font(8)).pack(anchor="w", pady=(4, 0))
        return lbl, bar

    def _game_row(self, parent, name):
        row = tk.Frame(self.game_rows, bg=T.BG1)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=name, bg=T.BG1, fg=T.TEXT_DIM,
                 font=font(9, True)).pack(side="left")
        val = tk.Label(row, text="--", bg=T.BG1, fg=T.TEXT,
                       font=font(9, mono=True))
        val.pack(side="right")
        return val

    def _chart_resize(self, e):
        try:
            self.chart.resize(e.width - 24, e.height - 58)
        except Exception:
            pass

    # ---------- updates ----------
    def update_stats(self, stats):
        try:
            self.cpu_lbl.configure(text=f"{stats.cpu:.0f}%")
            self.cpu_bar.set(stats.cpu)
            self.ram_lbl.configure(text=f"{stats.ram:.0f}%")
            self.ram_bar.set(stats.ram)
            if stats.gpu is None:
                self.gpu_lbl.configure(text=t("common.na"))
                self.gpu_bar.set(0)
            else:
                self.gpu_lbl.configure(text=f"{stats.gpu:.0f}%")
                self.gpu_bar.set(stats.gpu)
        except Exception:
            pass
        try:
            if stats.game_pid:
                self.game_dot.configure(fg=T.ACCENT)
                self.game_state.configure(text=t("dash.game.running"), fg=T.TEXT)
                self.game_name_lbl.configure(text=stats.game_name or "--")
                self.game_pid_lbl.configure(text=str(stats.game_pid))
                self.game_cpu_lbl.configure(text=f"{stats.game_cpu:.0f}%")
                self.game_prio_lbl.configure(text=str(stats.game_priority or "--"))
            else:
                self.game_dot.configure(fg=T.TEXT_FAINT)
                self.game_state.configure(text=t("dash.game.idle"), fg=T.TEXT_DIM)
                self.game_name_lbl.configure(text="--")
                self.game_pid_lbl.configure(text="--")
                self.game_cpu_lbl.configure(text="--")
                self.game_prio_lbl.configure(text="--")
        except Exception:
            pass

    def set_index(self, idx):
        try:
            self.gauge.set(idx)
        except Exception:
            pass

    def push_chart(self, v):
        try:
            self.chart.push(v)
        except Exception:
            pass

    def set_last_bench(self, text):
        try:
            self.last_bench_lbl.configure(text=text)
        except Exception:
            pass

    def set_boosting(self, v):
        try:
            if v:
                self.boost_btn.set_text(f"{t('dash.boosting')}...")
                self.bench_btn.set_enabled(False)
                self.status_lbl.configure(text="")
            else:
                self.boost_btn.set_text(t("dash.boost"))
                self.bench_btn.set_enabled(True)
                self.progress.set(0)
        except Exception:
            pass

    def set_progress(self, i, n, item_id):
        try:
            self.progress.set((i + 1) / max(1, n) * 100)
            self.status_lbl.configure(text=f"[{i + 1}/{n}] {item_id}")
        except Exception:
            pass

    def set_status(self, text):
        try:
            self.status_lbl.configure(text=text)
        except Exception:
            pass

    def set_bench_btn(self, running):
        try:
            self.bench_btn.set_text(t("dash.bench.run") if running else t("dash.bench"))
            self.boost_btn.set_enabled(not running)
        except Exception:
            pass
