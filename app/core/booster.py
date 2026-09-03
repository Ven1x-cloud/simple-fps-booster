"""Optimization engine.

Every optimization is reversible; previous values are persisted in
settings["prev"] so reverts survive an app restart. Registry work is
per-user (HKCU). The only admin item is pausing Windows services.
"""
import platform
import re
import subprocess

IS_WIN = platform.system() == "Windows"

HIGH_PERF_GUID = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"  # High Performance
_SERVICES = ("SysMain", "WSearch", "DiagTrack")
_SVC_TYPE = {"0": "boot", "1": "system", "2": "auto", "3": "demand", "4": "disabled"}


def _shell(cmd, timeout=25):
    """Run a command quietly. Returns (rc, stdout)."""
    kw = dict(capture_output=True, text=True, timeout=timeout)
    if IS_WIN:
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        r = subprocess.run(cmd, **kw)
        return r.returncode, (r.stdout or "")
    except Exception as e:
        return -1, str(e)


class Booster:
    def __init__(self, settings, log):
        self.settings = settings
        self.log = log
        self.prev = settings.get("prev", None) or {}

    # ---------- persistence of previous values ----------
    def _save_prev(self):
        self.settings.set("prev", self.prev)

    def _reg_get(self, path, name):
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as k:
                v, _ = winreg.QueryValueEx(k, name)
                return v
        except OSError:
            return None

    def _reg_set(self, path, name, value):
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as k:
            winreg.SetValueEx(k, name, 0, winreg.REG_DWORD, int(value))

    def _reg_apply(self, path, name, value):
        old = self._reg_get(path, name)
        self.prev[name] = {"path": path, "old": old}
        self._reg_set(path, name, value)
        self._save_prev()

    def _reg_revert(self, name):
        import winreg
        info = self.prev.get(name)
        if not info:
            return True, ""
        old = info.get("old")
        try:
            if old is None:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, info["path"], 0,
                                    winreg.KEY_SET_VALUE) as k:
                    winreg.DeleteValue(k, name)
            else:
                self._reg_set(info["path"], name, old)
        except OSError:
            pass
        self.prev.pop(name, None)
        self._save_prev()
        return True, ""

    def applied_ids(self):
        ids = set()
        if "AllowGameDVR" in self.prev:
            ids.add("gamedvr")
        if "GameDVR_Enabled" in self.prev:
            ids.add("gamebar")
        if "NoToastApplicationNotification" in self.prev:
            ids.add("notifications")
        if "power" in self.prev:
            ids.add("power")
        if "services" in self.prev:
            ids.add("services")
        return ids

    # ---------- individual items ----------
    def apply_priority(self):
        from .stats import SystemStats
        ok, msg = SystemStats().set_game_priority_high()
        return ok, msg

    def apply_gamedvr(self):
        self._reg_apply(r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
                        "AllowGameDVR", 0)
        return True, "Game DVR off"

    def apply_gamebar(self):
        self._reg_apply(r"System\GameConfigStore", "GameDVR_Enabled", 0)
        return True, "Game Bar off"

    def apply_notifications(self):
        self._reg_apply(r"Software\Microsoft\Windows\CurrentVersion\PushNotifications",
                        "NoToastApplicationNotification", 1)
        return True, "toasts silenced"

    def apply_power(self):
        rc, out = _shell(["powercfg", "/getactivescheme"])
        if rc == 0:
            m = re.search(
                r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
                out, re.I)
            if m:
                self.prev["power"] = {"guid": m.group(1)}
                self._save_prev()
        rc, out = _shell(["powercfg", "/setactive", HIGH_PERF_GUID])
        if rc != 0:
            return False, out.strip() or "powercfg failed"
        return True, "High Performance active"

    def revert_power(self):
        info = self.prev.get("power")
        if not info or not info.get("guid"):
            return True, ""
        rc, out = _shell(["powercfg", "/setactive", info["guid"]])
        if rc == 0:
            self.prev.pop("power", None)
            self._save_prev()
            return True, "previous plan restored"
        return False, out.strip() or "powercfg failed"

    def apply_services(self):
        if not IS_WIN:
            return False, "Windows only"
        results = []
        saved = self.prev.setdefault("services", {})
        for svc in _SERVICES:
            rc, out = _shell(["sc", "qc", svc])
            m = re.search(r"START_TYPE\s*:\s*(\d+)", out or "")
            saved[svc] = m.group(1) if m else "2"
            _shell(["sc", "stop", svc], timeout=15)
            rc3, out3 = _shell(["sc", "config", svc, "start=", "disabled"])
            results.append(svc if rc3 == 0 else f"{svc}!")
        self._save_prev()
        return True, ", ".join(results)

    def revert_services(self):
        info = self.prev.get("services") or {}
        for svc, st in info.items():
            _shell(["sc", "config", svc, "start=", _SVC_TYPE.get(st, "demand")])
            _shell(["sc", "start", svc], timeout=15)
        self.prev.pop("services", None)
        self._save_prev()
        return True, "services restored"

    def close_apps(self, names):
        try:
            import psutil
        except Exception:
            return False, "psutil not available"
        want = {(n or "").lower() for n in names}
        want.discard("")
        closed = []
        try:
            for p in psutil.process_iter(["name"]):
                try:
                    nm = (p.info.get("name") or "").lower()
                    if nm in want:
                        p.terminate()
                        closed.append(nm)
                except Exception:
                    continue
        except Exception as e:
            return False, str(e)
        return True, ", ".join(closed) if closed else "none running"

    # ---------- dispatch ----------
    def apply(self, item_id):
        if item_id == "priority":
            return self.apply_priority()
        if item_id == "autoprio":
            return True, "watcher active"
        if item_id == "gamedvr":
            if not IS_WIN:
                return False, "Windows only"
            return self.apply_gamedvr()
        if item_id == "gamebar":
            if not IS_WIN:
                return False, "Windows only"
            return self.apply_gamebar()
        if item_id == "notifications":
            if not IS_WIN:
                return False, "Windows only"
            return self.apply_notifications()
        if item_id == "power":
            if not IS_WIN:
                return False, "Windows only"
            return self.apply_power()
        if item_id == "services":
            return self.apply_services()
        if item_id == "killapps":
            return self.close_apps(self.settings.get("kill_list", []))
        return False, f"unknown item {item_id}"

    def revert(self, item_id):
        if item_id == "gamedvr":
            return self._reg_revert("AllowGameDVR")
        if item_id == "gamebar":
            return self._reg_revert("GameDVR_Enabled")
        if item_id == "notifications":
            return self._reg_revert("NoToastApplicationNotification")
        if item_id == "power":
            return self.revert_power()
        if item_id == "services":
            return self.revert_services()
        return True, ""

    def apply_all(self, enabled_ids, on_step=None):
        results = {}
        total = max(len(enabled_ids), 1)
        for i, item_id in enumerate(enabled_ids):
            if on_step:
                try:
                    on_step(i, total, item_id)
                except Exception:
                    pass
            try:
                ok, msg = self.apply(item_id)
            except Exception as e:
                ok, msg = False, str(e)
            results[item_id] = (ok, msg)
            (self.log.ok if ok else self.log.warn)(f"{item_id}: {msg}")
        return results

    def revert_all(self):
        for item_id in ("gamedvr", "gamebar", "notifications", "power", "services"):
            try:
                ok, msg = self.revert(item_id)
                if msg:
                    self.log.info(f"{item_id} reverted: {msg}")
                if not ok:
                    self.log.warn(f"{item_id} revert failed: {msg}")
            except Exception as e:
                self.log.warn(f"{item_id} revert error: {e}")
