#!/usr/bin/env python3
"""Neon FPS Booster - full installer.

Fetches the application code AND the install command manifest from the
selected GitHub repository, installs dependencies in an isolated venv,
creates desktop / start-menu shortcuts, optional startup entry, and can
launch the app.

Usage:
    python installer.py                            interactive
    python installer.py --yes                      defaults, no prompts
    python installer.py --repo owner/repo --branch main
    python installer.py --dry-run                  show what would happen
    python installer.py --startup --no-shortcut

One-liner (Windows 10+ cmd):
    curl -L https://github.com/Ven1x-cloud/simple-fps-booster/raw/main/installer.py -o installer.py && python installer.py

One-liner (PowerShell):
    powershell -NoProfile -c "iex ((New-Object Net.WebClient).DownloadString('https://github.com/Ven1x-cloud/simple-fps-booster/raw/main/installer.py'))"
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request

PRODUCT = "Neon FPS Booster"
VERSION = "2.0.0"
DEFAULT_REPO = "Ven1x-cloud/simple-fps-booster"
DEFAULT_BRANCH = "main"
IS_WIN = platform.system() == "Windows"
PY_MIN = (3, 9)


# ---------------------------------------------------------------- terminal
def _colors_on():
    try:
        return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    except Exception:
        return False


_ON = _colors_on()


def _c(code, s):
    return f"\033[{code}m{s}\033[0m" if _ON else s


def info(msg):
    print(_c("36", "  [..] ") + msg)


def ok(msg):
    print(_c("32", "  [OK] ") + msg)


def warn(msg):
    print(_c("33", "  [!!] ") + msg)


def err(msg):
    print(_c("31", "  [X]  ") + str(msg))


def step(n, total, msg):
    bar = "[" + _c("32", "#") * n + _c("90", "-") * (total - n) + "]"
    print(_c("1;32", f"\n {bar} STEP {n}/{total}  ") + msg)


BANNER = r"""
  ____   ___   ___ _  _   _    _  _   _____
 / __ \ / _ \ / __| || | / \  | || | |_   _|
| |  | | | | | (__| __ |/ _ \ | __ |   | |
|_|  |_|_| |_|\___|_||_/_/ \_\|_||_|   |_|

        F P S   B O O S T E R   v{v}
        P R O F E S S I O N A L   E D I T I O N
"""


def banner():
    print(_c("1;32", BANNER.format(v=VERSION)))


# ---------------------------------------------------------------- helpers
def prompt(msg, default=None):
    suffix = _c("90", f" [{default}]") if default else ""
    try:
        v = input(f"  {msg}{suffix}: ").strip()
    except EOFError:
        v = ""
    return v or (default or "")


def confirm(msg, default=False):
    d = "Y/n" if default else "y/N"
    v = prompt(msg, d)
    return v[:1].lower() in ("y", "j")


def run(cmd, cwd=None, timeout=600, quiet=False, shell=False):
    kw = dict(cwd=cwd, timeout=timeout)
    if IS_WIN:
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    if quiet:
        kw.update(capture_output=True, text=True)
    return subprocess.run(cmd if shell else cmd, shell=shell, **kw)


def default_install_dir():
    if IS_WIN:
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(base, "NeonFPSBooster")
    base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
    return os.path.join(base, "neon-fps-booster")


def venv_python(venv_dir):
    if IS_WIN:
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


def pythonw(venv_dir):
    if IS_WIN:
        p = os.path.join(venv_dir, "Scripts", "pythonw.exe")
        return p if os.path.exists(p) else venv_python(venv_dir)
    return venv_python(venv_dir)


# ---------------------------------------------------------------- repo
def parse_repo(spec):
    spec = (spec or "").strip().strip("/")
    if "://" in spec:
        spec = spec.split("://", 1)[1]
    if spec.startswith("git@"):
        spec = spec.split(":", 1)[1] if ":" in spec else spec
    if spec.lower().startswith("github.com/"):
        spec = spec[len("github.com/"):]
    parts = [p for p in spec.split("/") if p]
    if len(parts) >= 2:
        name = parts[1]
        if name.lower().endswith(".git"):
            name = name[:-4]
        return parts[0], name
    raise SystemExit(err(f"cannot parse repository '{spec}' - expected owner/name"))


def fetch_repo(owner, repo, branch, workdir, dry=False):
    """Clone (or tarball-download) the selected repository. Returns app dir."""
    dest = os.path.join(workdir, f"{owner}-{repo}-{branch}")
    if os.path.isdir(dest):
        shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(workdir, exist_ok=True)

    if shutil.which("git"):
        info(f"git clone https://github.com/{owner}/{repo} ({branch})")
        if not dry:
            cmd = ["git", "clone", "--depth", "1", "--branch", branch,
                   "--single-branch", f"https://github.com/{owner}/{repo}.git", dest]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if r.returncode == 0:
                ok("repository cloned")
                return dest
            warn(f"git clone failed ({r.stderr.strip()[:160]}) - trying tarball")

    url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{branch}"
    info(f"downloading {url}")
    if dry:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": f"{PRODUCT}-installer"})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = resp.read()
    except Exception as e:
        raise SystemExit(err(f"download failed: {e}"))
    tmp = dest + ".tgz"
    with open(tmp, "wb") as f:
        f.write(data)
    extracted = dest + "_x"
    with tarfile.open(tmp, "r:gz") as tf:
        try:
            tf.extractall(extracted, filter="data")
        except TypeError:  # Python < 3.11
            for m in tf.getmembers():
                parts = m.name.split("/")
                if m.name.startswith("/") or ".." in parts:
                    raise SystemExit(err("unsafe path in archive"))
            tf.extractall(extracted)
    os.remove(tmp)
    found = None
    for root, dirs, files in os.walk(extracted):
        if "main.py" in files:
            found = root
            break
    if found is None:
        shutil.rmtree(extracted, ignore_errors=True)
        raise SystemExit(err("repository does not contain main.py"))
    try:
        os.rename(found, dest)
    except OSError:
        shutil.move(found, dest)
    if found != extracted:
        shutil.rmtree(extracted, ignore_errors=True)
    ok("repository downloaded")
    return dest


def read_manifest(appdir):
    p = os.path.join(appdir, "installer_manifest.json")
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            warn(f"invalid manifest ({e}) - using defaults")
    return {}


def latest_commit(appdir):
    if not os.path.isdir(os.path.join(appdir, ".git")):
        return None
    try:
        r = subprocess.run(["git", "-C", appdir, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=20)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- install
def make_shortcut(path, target, args, workdir, icon=None):
    """Create a .lnk via PowerShell (Windows only)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    icon_line = f'$s.IconLocation = "{icon}",0' if icon else ""
    ps = (
        "$ws = New-Object -ComObject WScript.Shell\n"
        f'$s = $ws.CreateShortcut("{path}")\n'
        f'$s.TargetPath = "{target}"\n'
        f'$s.Arguments = "{args}"\n'
        f'$s.WorkingDirectory = "{workdir}"\n'
        f"{icon_line}\n"
        f'$s.Description = "{PRODUCT}"\n'
        "$s.Save()"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-Command", ps], capture_output=True, text=True, timeout=90)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(description=f"{PRODUCT} installer")
    ap.add_argument("--repo", default=None, help="GitHub repository (owner/name)")
    ap.add_argument("--branch", default=None, help="branch to install from")
    ap.add_argument("--dest", default=None, help="install directory")
    ap.add_argument("--yes", action="store_true", help="no prompts, accept defaults")
    ap.add_argument("--startup", action="store_true", help="add start-with-OS entry")
    ap.add_argument("--no-shortcut", action="store_true", help="skip shortcuts")
    ap.add_argument("--no-launch", action="store_true", help="do not offer to launch")
    ap.add_argument("--dry-run", action="store_true", help="show steps without doing them")
    args = ap.parse_args()
    dry = args.dry_run

    banner()
    info(f"{PRODUCT} v{VERSION} - full installer")
    info(f"python {sys.version.split()[0]} | {platform.system()} {platform.release()}")

    if sys.version_info < PY_MIN:
        err(f"Python >= {PY_MIN[0]}.{PY_MIN[1]} is required")
        sys.exit(1)

    total = 8

    # 1 - select repository
    step(1, total, "SELECT REPOSITORY")
    repo_spec = args.repo
    if repo_spec is None and not args.yes:
        repo_spec = prompt("Repository (owner/name)", DEFAULT_REPO)
    repo_spec = repo_spec or DEFAULT_REPO
    branch = args.branch
    if branch is None and not args.yes:
        branch = prompt("Branch", DEFAULT_BRANCH)
    branch = branch or DEFAULT_BRANCH
    owner, repo = parse_repo(repo_spec)
    ok(f"{owner}/{repo} @ {branch}")

    # 2 - fetch code + commands from the repository
    step(2, total, "FETCH CODE + COMMANDS FROM REPOSITORY")
    workdir = os.path.join(os.environ.get("TEMP") or os.environ.get("TMP") or
                           "/tmp", "neon-fps-install")
    src = fetch_repo(owner, repo, branch, workdir, dry=dry)
    manifest = {} if dry else read_manifest(src)
    commit = None if dry else latest_commit(src)
    ok(f"source ready {('(' + commit + ')') if commit else ''}".rstrip() +
       ("" if dry else ""))

    # 3 - layout
    step(3, total, "PREPARE INSTALL LAYOUT")
    install_dir = args.dest or default_install_dir()
    appdir = os.path.join(install_dir, "app")
    venv_dir = os.path.join(install_dir, "venv")
    if not dry:
        if os.path.isdir(appdir):
            shutil.rmtree(appdir, ignore_errors=True)
        shutil.copytree(src, appdir,
                        ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                      "*.pyc", "venv"))
    ok(f"app -> {appdir}")
    ok(f"venv -> {venv_dir}")

    # 4 - python environment + dependencies
    step(4, total, "PYTHON VENV + DEPENDENCIES")
    vpy = venv_python(venv_dir)
    if not dry:
        if os.path.isdir(venv_dir):
            shutil.rmtree(venv_dir, ignore_errors=True)
        info("creating venv")
        r = subprocess.run([sys.executable, "-m", "venv", venv_dir],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise SystemExit(err(f"venv creation failed:\n{r.stderr[-400:]}"))
        info("upgrading pip")
        subprocess.run([vpy, "-m", "pip", "install", "-q", "-U", "pip"],
                       capture_output=True, timeout=600)
        req = os.path.join(appdir, "requirements.txt")
        if os.path.isfile(req):
            info("installing requirements.txt")
            r = subprocess.run([vpy, "-m", "pip", "install", "-q", "-r", req],
                               capture_output=True, text=True, timeout=900)
            if r.returncode != 0:
                warn(f"pip install reported errors:\n{r.stderr[-400:]}")
            else:
                ok("dependencies installed")
        else:
            warn("no requirements.txt found - installing standard deps")
            r = subprocess.run([vpy, "-m", "pip", "install", "-q",
                                "psutil", "Pillow"],
                               capture_output=True, text=True, timeout=900)
            ok("dependencies installed") if r.returncode == 0 else warn("pip failed")
    else:
        info("dry-run: skip venv + pip")

    # 5 - app icon
    step(5, total, "APP ICON")
    ico = os.path.join(appdir, "assets", "app.ico")
    logo = os.path.join(appdir, "assets", "logo.png")
    icon_path = ico if os.path.isfile(ico) else None
    if icon_path is None and os.path.isfile(logo) and not dry:
        script = os.path.join(appdir, "scripts", "make_icon.py")
        if os.path.isfile(script):
            r = subprocess.run([vpy, script], capture_output=True, text=True,
                               timeout=120, cwd=appdir)
            if r.returncode == 0 and os.path.isfile(ico):
                ok("icon generated from logo.png")
            else:
                warn("icon generation skipped")
        else:
            warn("no icon script - shortcuts use default icon")
    if icon_path:
        ok(icon_path)
    else:
        info("no icon (default will be used)")

    # 6 - manifest commands
    step(6, total, "RUN REPOSITORY INSTALL COMMANDS")
    commands = manifest.get("commands", [])
    if not commands:
        info("manifest has no extra commands - nothing to run")
    for i, c in enumerate(commands, 1):
        if not isinstance(c, dict) or not c.get("cmd"):
            continue
        desc = c.get("desc", c["cmd"])
        info(f"{i}/{len(commands)}: {desc}")
        if dry:
            continue
        if c.get("admin") and IS_WIN:
            try:
                import ctypes
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    if not c.get("optional", True) or confirm(f"admin needed: {desc}", True):
                        pass
                    if not ctypes.windll.shell32.IsUserAnAdmin():
                        warn("not elevated - skipped")
                        continue
            except Exception:
                pass
        r = run(c["cmd"], cwd=c.get("cwd") or appdir, timeout=c.get("timeout", 600),
                quiet=bool(c.get("quiet")), shell=True)
        if r.returncode != 0:
            if c.get("optional", True):
                warn(f"optional command failed (rc={r.returncode})")
            else:
                raise SystemExit(err(f"command failed: {desc}"))
    ok("commands complete")

    # 7 - shortcuts
    step(7, total, "SHORTCUTS")
    shortcuts = manifest.get("shortcuts", {})
    name = shortcuts.get("name", PRODUCT)
    launched_target = os.path.join(appdir, "main.py")
    created = []
    if IS_WIN and not args.no_shortcut and not dry:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop", f"{name}.lnk")
        if shortcuts.get("desktop", True) and make_shortcut(
                desktop, pythonw(venv_dir), f'"{launched_target}"',
                appdir, icon_path):
            ok(desktop)
            created.append(desktop)
        sm_dir = os.path.join(os.environ.get("APPDATA", ""),
                              "Microsoft", "Windows", "Start Menu", "Programs", name)
        sm = os.path.join(sm_dir, f"{name}.lnk")
        if shortcuts.get("startmenu", True) and make_shortcut(
                sm, pythonw(venv_dir), f'"{launched_target}"', appdir, icon_path):
            ok(sm)
            created.append(sm)
        unlnk = os.path.join(sm_dir, "Uninstall Neon FPS Booster.lnk")
        if make_shortcut(unlnk, pythonw(venv_dir),
                         f'"{os.path.join(appdir, "uninstall.py")}"',
                         appdir, icon_path):
            ok(unlnk)
    elif not IS_WIN and not dry:
        ok(f"run with: {venv_python(venv_dir)} \"{launched_target}\"")
    else:
        info("dry-run or skipped")

    # 8 - startup + state + launch
    step(8, total, "STARTUP + FINISH")
    want_startup = args.startup
    if not args.yes and not args.no_launch and not dry:
        if not want_startup:
            want_startup = confirm("Start Neon FPS Booster with Windows?", False)
    if want_startup and not dry:
        if IS_WIN:
            start_dir = os.path.join(os.environ.get("APPDATA", ""),
                                     "Microsoft", "Windows", "Start Menu",
                                     "Programs", "Startup")
            if make_shortcut(os.path.join(start_dir, f"{name}.lnk"),
                             pythonw(venv_dir), f'"{launched_target}"',
                             appdir, icon_path):
                ok("startup entry created")
        else:
            autostart = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart, exist_ok=True)
            dp = os.path.join(autostart, "neon-fps-booster.desktop")
            with open(dp, "w", encoding="utf-8") as f:
                f.write("[Desktop Entry]\nType=Application\nName=Neon FPS Booster\n")
                f.write(f'Exec={venv_python(venv_dir)} "{launched_target}"\n')
                f.write(f"Path={appdir}\nTerminal=false\n")
            ok("startup entry created")
    else:
        info("no startup entry")

    if not dry:
        state = {"product": PRODUCT, "version": VERSION, "repo": repo_spec,
                 "branch": branch, "commit": commit, "install_dir": install_dir,
                 "appdir": appdir, "venv": venv_dir, "shortcuts": created,
                 "installed": platform.node()}
        with open(os.path.join(install_dir, "install.json"), "w",
                  encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    print(_c("1;32", "\n" + "=" * 58))
    ok(f"{PRODUCT} v{VERSION} installed")
    info(f"repository : {owner}/{repo} @ {branch} {('(' + commit + ')') if commit else ''}".rstrip())
    info(f"install dir: {install_dir}")
    if IS_WIN:
        info(f"launch    : {pythonw(venv_dir)} \"{launched_target}\"")
    if not dry and not args.no_launch and not args.yes:
        if confirm("Launch Neon FPS Booster now?", True):
            subprocess.Popen([pythonw(venv_dir), launched_target], cwd=appdir,
                             creationflags=0x08000000 if IS_WIN else 0)
            ok("launched")
    print(_c("1;32", "=" * 58) + "\n")


if __name__ == "__main__":
    main()
