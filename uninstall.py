#!/usr/bin/env python3
"""Neon FPS Booster - uninstaller.

Removes shortcuts, the startup entry and the install directory.
User settings (in %APPDATA%/NeonFPSBooster) are kept unless --purge.
"""
import json
import os
import platform
import shutil
import sys

IS_WIN = platform.system() == "Windows"
PRODUCT = "Neon FPS Booster"


def default_install_dir():
    if IS_WIN:
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(base, "NeonFPSBooster")
    base = os.environ.get("XDG_DATA_HOME",
                          os.path.join(os.path.expanduser("~"), ".local", "share"))
    return os.path.join(base, "neon-fps-booster")


def read_state(install_dir):
    p = os.path.join(install_dir, "install.json")
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def confirm(msg, default=True):
    d = "Y/n" if default else "y/N"
    try:
        v = input(f"  {msg} [{d}]: ").strip()
    except EOFError:
        v = ""
    return (v or ("y" if default else "n"))[:1].lower() in ("y", "j")


def main():
    purge = "--purge" in sys.argv
    quiet = "--yes" in sys.argv
    print(f"{PRODUCT} - uninstaller")
    install_dir = default_install_dir()
    if len(sys.argv) > 1 and sys.argv[1].startswith("--dest="):
        install_dir = sys.argv[1].split("=", 1)[1]
    state = read_state(install_dir)
    print(f"  install dir : {install_dir}")
    print(f"  repository  : {state.get('repo', '?')} @ {state.get('branch', '?')}")

    if not quiet:
        if not confirm("Uninstall Neon FPS Booster?", True):
            print("  cancelled")
            return

    removed = []

    # shortcuts
    for sc in state.get("shortcuts", []) or []:
        try:
            if os.path.isfile(sc):
                os.remove(sc)
                removed.append(sc)
        except Exception:
            pass
    if IS_WIN:
        sm = os.path.join(os.environ.get("APPDATA", ""),
                          "Microsoft", "Windows", "Start Menu", "Programs",
                          "Neon FPS Booster")
        for p in (os.path.join(sm, "Neon FPS Booster.lnk"),
                  os.path.join(sm, "Uninstall Neon FPS Booster.lnk")):
            try:
                if os.path.isfile(p):
                    os.remove(p)
                    removed.append(p)
            except Exception:
                pass
        try:
            if os.path.isdir(sm) and not os.listdir(sm):
                os.rmdir(sm)
        except Exception:
            pass
        startup = os.path.join(os.environ.get("APPDATA", ""),
                               "Microsoft", "Windows", "Start Menu",
                               "Programs", "Startup", "Neon FPS Booster.lnk")
        try:
            if os.path.isfile(startup):
                os.remove(startup)
                removed.append(startup)
        except Exception:
            pass
    else:
        for p in (os.path.expanduser("~/.config/autostart/neon-fps-booster.desktop"),):
            try:
                if os.path.isfile(p):
                    os.remove(p)
                    removed.append(p)
            except Exception:
                pass

    # install directory
    if os.path.isdir(install_dir):
        try:
            shutil.rmtree(install_dir)
            removed.append(install_dir)
        except Exception as e:
            print(f"  [!!] could not remove {install_dir}: {e}")

    # settings
    if IS_WIN:
        settings = os.path.join(os.environ.get("APPDATA", ""), "NeonFPSBooster")
    else:
        settings = os.path.join(os.path.expanduser("~"), ".config", "NeonFPSBooster")
    if purge and os.path.isdir(settings):
        try:
            shutil.rmtree(settings)
            removed.append(settings)
        except Exception:
            pass
    elif os.path.isdir(settings):
        print(f"  kept settings: {settings} (use --purge to delete)")

    for p in removed:
        print(f"  [OK] removed {p}")
    print("\n  done.")


if __name__ == "__main__":
    main()
