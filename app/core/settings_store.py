"""Persistent JSON settings (per-user)."""
import json
import os
import threading
import sys


def app_data_dir():
    """Per-user data directory for settings."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    d = os.path.join(base, "NeonFPSBooster")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


DEFAULTS = {
    "lang": "auto",                      # auto | en | nl
    "repo": "Ven1x-cloud/simple-fps-booster",
    "branch": "main",
    "startup": False,
    "opt": {
        "priority": False,
        "autoprio": True,
        "gamedvr": False,
        "gamebar": False,
        "notifications": False,
        "power": False,
        "services": False,
        "killapps": False,
    },
    "kill_list": [
        "Spotify.exe", "Discord.exe", "Teams.exe",
        "OneDrive.exe", "Steam.exe", "EpicGamesLauncher.exe",
    ],
    "prev": {},          # saved previous values used by reverts
    "last_update": None,
    "bench_best": None,
}


class Settings:
    """Thread-safe JSON settings with dot-path access."""

    def __init__(self, path=None):
        self.path = path or os.path.join(app_data_dir(), "settings.json")
        self._lock = threading.RLock()
        self.data = json.loads(json.dumps(DEFAULTS))
        self.load()

    # ---------- io ----------
    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                stored = json.load(f)
            self._merge(self.data, stored)
        except Exception:
            pass
        self._save()  # normalize the file on disk

    def _merge(self, dst, src):
        if not isinstance(src, dict):
            return
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                self._merge(dst[k], v)
            else:
                dst[k] = v

    def _save(self):
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

    # ---------- access ----------
    def get(self, key, default=None):
        with self._lock:
            node = self.data
            for part in key.split("."):
                if not isinstance(node, dict) or part not in node:
                    return default
                node = node[part]
            return node

    def set(self, key, value):
        with self._lock:
            parts = key.split(".")
            node = self.data
            for p in parts[:-1]:
                node = node.setdefault(p, {})
            node[parts[-1]] = value
            self._save()

    def reset(self):
        with self._lock:
            self.data = json.loads(json.dumps(DEFAULTS))
            self._save()
