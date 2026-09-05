"""Micro-benchmarks.

- run_cpu_bench: pure CPU throughput test (worker thread), MOp/s.
- RenderTest: timed main-thread canvas draw loop, reports FPS.
- performance_index: composite 0..999 "FPS Index" used by the dashboard.
"""
import math
import time


def run_cpu_bench(duration=1.0, stop_flag=None):
    """Run a CPU-bound workload for `duration` seconds. Returns MOp/s."""
    start = time.perf_counter()
    end = start + duration
    x = 0.75
    ops = 0
    while True:
        if time.perf_counter() >= end:
            break
        if stop_flag is not None and stop_flag():
            break
        for _ in range(20000):
            x += math.sin(x) * 0.5 + math.sqrt(abs(x) + 1e-9)
            ops += 2
            if math.isnan(x):
                x = 0.75
    elapsed = max(time.perf_counter() - start, 1e-6)
    return ops / elapsed / 1e6


def performance_index(mopss, draw_fps=0.0):
    """Composite performance index (0..999) from CPU + UI render throughput."""
    return int(round(min(999.0, mopss * 12.0 + draw_fps * 6.0)))


class RenderTest:
    """Timed main-thread render loop over a Tk canvas.

    Moves a field of small rectangles across the canvas, which exercises
    Tk's draw path the way an in-game overlay would. Reports FPS through
    on_done(fps) on the main thread when the duration elapses.
    """

    TAG = "rt"

    def __init__(self, canvas, duration=2.0, shapes=90, on_done=None):
        self.canvas = canvas
        self.duration = duration
        self.shapes = shapes
        self.on_done = on_done
        self._running = False
        self._frames = 0
        self._t0 = 0.0
        self._pos = []
        self._vel = []

    def start(self):
        if self._running:
            return
        self._running = True
        self._frames = 0
        self._t0 = time.perf_counter()
        c = self.canvas
        w = c.winfo_width() or 300
        h = c.winfo_height() or 150
        self._w = max(w, 20)
        self._h = max(h, 20)
        import random
        rng = random.Random(1337)
        self._pos = [(rng.uniform(0, self._w - 6), rng.uniform(0, self._h - 6))
                     for _ in range(self.shapes)]
        self._vel = [(rng.uniform(-3.5, 3.5), rng.uniform(-3.5, 3.5))
                     for _ in range(self.shapes)]
        self._step()

    def _step(self):
        if not self._running:
            return
        if time.perf_counter() - self._t0 >= self.duration:
            self._finish()
            return
        c = self.canvas
        w, h = self._w, self._h
        try:
            c.delete(self.TAG)
            for i in range(len(self._pos)):
                x, y = self._pos[i]
                vx, vy = self._vel[i]
                x += vx
                y += vy
                if x < 0 or x > w - 6:
                    vx = -vx
                    x = max(0.0, min(w - 6, x))
                if y < 0 or y > h - 6:
                    vy = -vy
                    y = max(0.0, min(h - 6, y))
                self._pos[i] = (x, y)
                self._vel[i] = (vx, vy)
                c.create_rectangle(x, y, x + 6, y + 6,
                                   fill="#00ff85", outline="", tags=self.TAG)
            self._frames += 1
        except Exception:
            self._finish()
            return
        try:
            c.after(1, self._step)
        except Exception:
            self._finish()

    def _finish(self):
        if not self._running:
            return
        self._running = False
        try:
            self.canvas.delete(self.TAG)
        except Exception:
            pass
        fps = self._frames / max(self.duration, 1e-6)
        if self.on_done:
            try:
                self.on_done(fps)
            except Exception:
                pass

    def cancel(self):
        self._running = False
        try:
            self.canvas.delete(self.TAG)
        except Exception:
            pass
