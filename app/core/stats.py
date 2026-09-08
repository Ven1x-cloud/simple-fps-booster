"""Live system statistics: CPU / RAM / GPU / Roblox game process."""
import platform
import shutil
import subprocess
import time

try:
    import psutil
except Exception:  # pragma: no cover - psutil is optional at runtime
    psutil = None

IS_WIN = platform.system() == "Windows"

# known Roblox client process names (lower-case)
GAME_NAMES = {
    "robloxplayerbeta.exe",
    "roblox.exe",
    "robloxplayer.exe",
    "roblox_studio.exe",
}

_WIN_PRIO = {
    0: "Idle",
    2: "Normal",
    3: "High",
    6: "Below Normal",
    7: "Above Normal",
    24: "Realtime",
}


def _run_quiet(cmd, timeout=2.5):
    kw = dict(capture_output=True, text=True, timeout=timeout)
    if IS_WIN:
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        r = subprocess.run(cmd, **kw)
        return r.returncode, (r.stdout or "")
    except Exception:
        return -1, ""


class SystemStats:
    """Sampled system state. Call refresh() from a worker thread."""

    def __init__(self):
        self.available = psutil is not None
        self.cpu = 0.0
        self.ram = 0.0
        self.gpu = None            # float 0-100 or None (unsupported)
        self.game_pid = None
        self.game_name = None
        self.game_cpu = 0.0
        self.game_priority = None
        self._gpu_cache = None
        self._gpu_at = 0.0
        if self.available:
            try:
                psutil.cpu_percent(interval=None)  # prime
            except Exception:
                pass

    # ---------- sampling ----------
    def refresh(self):
        if not self.available:
            return
        try:
            self.cpu = psutil.cpu_percent(interval=None)
        except Exception:
            self.cpu = 0.0
        try:
            self.ram = psutil.virtual_memory().percent
        except Exception:
            self.ram = 0.0
        now = time.time()
        if now - self._gpu_at >= 2.0:
            self._gpu_at = now
            self._gpu_cache = self._query_gpu()
        self.gpu = self._gpu_cache
        self._refresh_game()

    def _query_gpu(self):
        exe = shutil.which("nvidia-smi")
        if not exe:
            return None
        try:
            rc, out = _run_quiet([exe, "--query-gpu=utilization.gpu",
                                  "--format=csv,noheader,nounits"])
            if rc == 0 and out.strip():
                return float(out.strip().splitlines()[0])
        except Exception:
            pass
        return None

    def _refresh_game(self):
        found = None
        try:
            for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
                try:
                    name = p.info.get("name") or ""
                    if name.lower() in GAME_NAMES:
                        found = p
                        break
                except Exception:
                    continue
        except Exception:
            found = None
        if found is None:
            self.game_pid = None
            self.game_name = None
            self.game_cpu = 0.0
            self.game_priority = None
            return
        self.game_pid = found.info.get("pid")
        self.game_name = found.info.get("name")
        self.game_cpu = found.info.get("cpu_percent") or 0.0
        self.game_priority = self._priority_label(found)

    @staticmethod
    def _priority_label(proc):
        try:
            if IS_WIN:
                return _WIN_PRIO.get(proc.priority(), "Normal")
            return f"nice {proc.nice()}"
        except Exception:
            return None

    # ---------- actions ----------
    def find_game(self):
        """Return the running Roblox psutil.Process, or None."""
        if not self.available:
            return None
        try:
            for p in psutil.process_iter(["name"]):
                try:
                    if (p.info.get("name") or "").lower() in GAME_NAMES:
                        return p
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def set_game_priority_high(self):
        """Set HIGH priority on the running Roblox process."""
        proc = self.find_game()
        if proc is None:
            return False, "not running"
        try:
            if IS_WIN:
                proc.nice(3)  # HIGH_PRIORITY_CLASS
            else:
                proc.nice(0)
            return True, f"{proc.name()} -> High"
        except Exception as e:
            return False, str(e)

    def set_game_affinity_all(self):
        """Lift any CPU-core restriction on the game (all cores again)."""
        proc = self.find_game()
        if proc is None:
            return False, "not running"
        try:
            cur = proc.cpu_affinity()
            n = psutil.cpu_count() or len(cur)
            if len(cur) < n:
                proc.cpu_affinity(list(range(n)))
                return True, f"affinity -> {n} cores"
            return True, "affinity ok"
        except Exception as e:
            return False, str(e)

    def game_timer_resolution(self, enabled):
        """Request 1 ms timer resolution while the game runs.

        Windows coalesces timers to ~15 ms when idle, which shows up as
        uneven frame pacing in games. timeBeginPeriod/timeEndPeriod are
        reference-counted, so callers should pair one of each.
        """
        if not IS_WIN:
            return False, "Windows only"
        try:
            import ctypes
            winmm = ctypes.windll.winmm
            if enabled:
                winmm.timeBeginPeriod(1)
                return True, "1ms timer on"
            winmm.timeEndPeriod(1)
            return True, "timer restored"
        except Exception as e:
            return False, str(e)
