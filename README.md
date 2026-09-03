<div align="center">

# ⚡ NEON FPS BOOSTER

### PROFESSIONAL EDITION — v2.0.0

**Neon technical-green performance suite for Roblox on Windows.**

Custom app frame • vector + PNG logo • live FPS index • 1-click boost •
full installer that pulls code **and** install commands from a selected GitHub repository

</div>

---

## ✨ Snel starten / Quick start (Nederlands)

1. Dubbelklik op `install.bat` (of `python installer.py`).
2. Kies de repository (standaard: `Ven1x-cloud/simple-fps-booster`) en branch.
3. Klaar — icoon op het bureaublad, app starten.

Installer werkt door de **code én de opdrachten** (`installer_manifest.json`) op te halen
uit de geselecteerde repository, dependencies in een geïsoleerde venv te installeren,
shortcuts te maken en optioneel de app te starten.

```bat
:: of met één regel in een terminal:
curl -L https://github.com/Ven1x-cloud/simple-fps-booster/raw/main/installer.py -o installer.py
python installer.py
```

## ✨ Features

- **Professional app frame** — frameless custom title bar (drag, minimize, maximize,
  close), taskbar entry kept, DPI aware, splash screen.
- **Logo** — generated neon emblem (`assets/logo.png`) + vector fallback drawn in-app;
  converted to `assets/app.ico` for the desktop shortcut.
- **Neon technical green theme** — dark green-tinted UI, accent `#00ff85`.
- **Dashboard** — live FPS Index gauge, CPU / RAM / GPU meters (NVIDIA via `nvidia-smi`),
  Roblox process monitor (PID, priority, CPU), live performance history chart.
- **1-click Boost** — measures a benchmark *before*, applies your selected
  optimizations, benchmarks *after*, and shows the real delta in a result modal.
- **Benchmark** — CPU micro-benchmark + live main-thread render test (visible on the
  chart while it runs).
- **Optimizer** (all reversible, per-user, no system tampering):
  | Item | What it does |
  |---|---|
  | Roblox priority → HIGH | sets the game process to `HIGH_PRIORITY_CLASS` |
  | Auto game mode | watcher keeps Roblox at HIGH while it runs |
  | Disable Game DVR | stops the hidden background screen recorder |
  | Disable Xbox Game Bar | removes overlay hooks |
  | Silence toasts | suppresses popup notifications |
  | High Performance plan | `powercfg` scheme switch (previous plan is saved) |
  | Pause services | SysMain / WSearch / DiagTrack (admin, restored later) |
  | Close background apps | closes the app list you choose in Settings |
- **Settings** — repository + branch for updates, English / Nederlands UI
  (auto-detects system language), start with Windows, background-app list, factory reset.
- **Activity log** — timestamped, colorized, save to file.
- **Updates from the repository** — in-app *Fetch latest* re-downloads the selected
  repo (git clone → tarball fallback).

## 🧩 Installer

`installer.py` is fully self-contained (standard library only) and works like this:

1. **Select repository** — default `Ven1x-cloud/simple-fps-booster`, or paste any
   `owner/name` (and branch) you want.
2. **Fetch** — `git clone --depth 1` first, codeload tarball download as fallback.
3. **Read `installer_manifest.json`** from the fetched repository — this file carries
   product info, shortcut settings and the **commands** to run:

   ```json
   "commands": [
     { "cmd": "echo hello", "desc": "example", "optional": true,
       "admin": false, "quiet": false, "cwd": "app", "timeout": 600 }
   ]
   ```
4. **Install** — copies the code to `%LOCALAPPDATA%\NeonFPSBooster\app`,
   creates an isolated venv and installs `requirements.txt`
   (`psutil`, `Pillow`).
5. **Icon** — generates `assets/app.ico` from `assets/logo.png`.
6. **Shortcuts** — Desktop, Start menu, Uninstall entry (`.lnk` via PowerShell).
7. **Startup** — optional start-with-Windows entry.
8. **State + launch** — writes `install.json` (used by `uninstall.py`), offers to launch.

CLI:

```bat
python installer.py                     :: interactive
python installer.py --yes               :: no prompts
python installer.py --repo owner/repo --branch dev
python installer.py --dry-run           :: show the plan only
python uninstall.py                     :: remove everything
python uninstall.py --purge --yes       :: also delete settings
```

> A repository used by the installer must contain `main.py` and
> `installer_manifest.json`. Anything else in the repo is installed as-is.

## 🚀 Run from source (development)

```bash
python -m pip install -r requirements.txt
python main.py            # GUI
python main.py --bench    # CLI micro-benchmark
python main.py --version
```

##  Project layout

```
main.py                    app entry point (Tk GUI)
app/
  theme.py                 neon green theme + geometry
  i18n.py                  EN/NL translations (auto-detect)
  core/
    stats.py               CPU/RAM/GPU + Roblox process sampling
    benchmark.py           CPU micro-bench + render FPS test
    booster.py             optimization engine (reversible)
    repo.py                GitHub fetch (git → tarball fallback)
    settings_store.py      JSON settings (%APPDATA%\NeonFPSBooster)
    logstore.py            activity log
    startup.py             start-with-OS management
  ui/
    frame.py               custom frameless window + title bar
    widgets.py             cards, neon buttons, toggles, gauge, chart
    logo.py                vector emblem + PNG loader
    dashboard.py           main page
    optimizer.py           optimization toggles
    settings_page.py       repo / language / general / apps
    logpage.py             activity log
installer.py               full installer (repo fetch + manifest commands)
uninstall.py               uninstaller
install.bat                double-click wrapper (Windows)
installer_manifest.json    product info + install commands for the installer
assets/logo.png            neon emblem (app.ico generated from it)
```

## ⚠️ Notes

- **Not affiliated with Roblox Corporation.** This is a system-optimization tool:
  it only changes per-user Windows settings, power plans and process priority,
  and every change can be reverted from the app (*Restore Defaults* / `uninstall.py`).
  It does not modify Roblox game files.
- Advanced service pausing requires running as administrator.
- GPU meter uses `nvidia-smi` when present (NVIDIA). AMD/Intel show `n/a`.
- Settings live in `%APPDATA%\NeonFPSBooster\settings.json` (Windows).
