"""In-memory activity log with subscriber callbacks (thread-safe)."""
import datetime
import threading
import time


class LogStore:
    def __init__(self, maxlen=600):
        self._entries = []
        self._subs = []
        self._lock = threading.Lock()
        self.maxlen = maxlen

    # ---------- pub/sub ----------
    def subscribe(self, fn):
        if fn not in self._subs:
            self._subs.append(fn)

    def unsubscribe(self, fn):
        try:
            self._subs.remove(fn)
        except ValueError:
            pass

    # ---------- write ----------
    def log(self, level, msg):
        entry = {"ts": time.time(), "level": level, "msg": str(msg)}
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self.maxlen:
                del self._entries[: len(self._entries) - self.maxlen]
        for fn in list(self._subs):
            try:
                fn(entry)
            except Exception:
                pass

    def info(self, msg):
        self.log("info", msg)

    def ok(self, msg):
        self.log("ok", msg)

    def warn(self, msg):
        self.log("warn", msg)

    def error(self, msg):
        self.log("error", msg)

    # ---------- read ----------
    def entries(self):
        with self._lock:
            return list(self._entries)

    def clear(self):
        with self._lock:
            self._entries.clear()

    def save(self, path):
        with self._lock:
            with open(path, "w", encoding="utf-8") as f:
                for e in self._entries:
                    stamp = datetime.datetime.fromtimestamp(e["ts"]).strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{stamp}  {e['level'].upper():5}  {e['msg']}\n")
        return path
