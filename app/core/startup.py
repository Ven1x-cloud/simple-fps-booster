"""Start-with-OS shortcut management (Windows: shell:startup, else .desktop)."""
import os
import platform
import subprocess
import sys

IS_WIN = platform.system() == "Windows"


def _pythonw():
    exe = sys.executable or "python"
    base, _ = os.path.splitext(exe)
    if IS_WIN:
        cand = base + "w.exe"
        if os.path.exists(cand):
            return cand
        if os.path.basename(exe).startswith("python"):
            return cand  # may not exist; installer recreates shortcuts anyway
    return exe


def main_py():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "main.py")


def startup_path():
    if IS_WIN:
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(appdata, "Microsoft", "Windows", "Start Menu",
                            "Programs", "Startup", "Neon FPS Booster.lnk")
    d = os.path.expanduser("~/.config/autostart")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return os.path.join(d, "neon-fps-booster.desktop")


def _powershell_shortcut(path, target, args, workdir, icon=None):
    icon_line = f'$s.IconLocation = "{icon}",0' if icon else ""
    ps = (
        "$ws = New-Object -ComObject WScript.Shell\n"
        f'$s = $ws.CreateShortcut("{path}")\n'
        f'$s.TargetPath = "{target}"\n'
        f'$s.Arguments = "{args}"\n'
        f'$s.WorkingDirectory = "{workdir}"\n'
        f"{icon_line}\n"
        '$s.Description = "Neon FPS Booster"\n'
        "$s.Save()"
    )
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-Command", ps],
        capture_output=True, text=True, timeout=60)
    return r.returncode == 0


def _write_desktop_entry(path):
    main = main_py()
    work = os.path.dirname(main)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("[Desktop Entry]\n")
        f.write("Type=Application\n")
        f.write("Name=Neon FPS Booster\n")
        f.write(f"Exec={sys.executable} \"{main}\"\n")
        f.write(f"Path={work}\n")
        f.write("Terminal=false\n")
        f.write("Comment=Neon FPS Booster\n")


def is_enabled():
    return os.path.exists(startup_path())


def set_enabled(enabled):
    path = startup_path()
    try:
        if not enabled:
            if os.path.exists(path):
                os.remove(path)
            return True
        if os.path.exists(path):
            return True
        if IS_WIN:
            return _powershell_shortcut(path, _pythonw(),
                                         f"\"{main_py()}\"",
                                         os.path.dirname(main_py()))
        _write_desktop_entry(path)
        return True
    except Exception:
        return False
