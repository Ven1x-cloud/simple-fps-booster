"""Lightweight EN/NL translations with automatic locale detection."""
import locale

_EN = {
    "titlebar.app": "NEON FPS BOOSTER",
    "titlebar.tagline": "PROFESSIONAL EDITION",

    "nav.dashboard": "Dashboard",
    "nav.optimizer": "Optimizer",
    "nav.settings": "Settings",
    "nav.log": "Log",

    "dash.status": "SYSTEM STATUS",
    "dash.fps": "FPS INDEX",
    "dash.fps.sub": "live micro-benchmark",
    "dash.cpu": "CPU",
    "dash.ram": "RAM",
    "dash.gpu": "GPU",
    "dash.load": "load",
    "dash.boost": "OPTIMIZE NOW",
    "dash.boost.sub": "1-click performance boost",
    "dash.boosting": "BOOSTING",
    "dash.bench": "RUN BENCHMARK",
    "dash.bench.run": "BENCHMARK RUNNING",
    "dash.last": "last full benchmark",
    "dash.game": "GAME PROCESS",
    "dash.game.running": "Roblox detected",
    "dash.game.idle": "Roblox not running",
    "dash.game.name": "Name",
    "dash.game.prio": "Priority",
    "dash.game.cpu": "CPU",
    "dash.game.pid": "PID",
    "dash.game.apply": "SET HIGH NOW",
    "dash.history": "PERFORMANCE HISTORY",
    "dash.history.sub": "performance index - live",

    "opt.title": "OPTIMIZER",
    "opt.apply": "APPLY ALL",
    "opt.revert": "RESTORE DEFAULTS",
    "opt.applied": "APPLIED",
    "opt.off": "OFF",
    "opt.on": "ON",
    "opt.admin": "ADMIN",
    "opt.error": "ERROR",
    "opt.sec.game": "GAME MODE",
    "opt.sec.win": "WINDOWS",
    "opt.sec.adv": "ADVANCED",
    "opt.admin.hint": "Advanced items require running as administrator.",
    "opt.items.priority": "Roblox priority to HIGH",
    "opt.desc.priority": "Boosts the game process above background tasks.",
    "opt.items.autoprio": "Auto game mode",
    "opt.desc.autoprio": "Keeps Roblox at HIGH priority while it runs.",
    "opt.items.gamedvr": "Disable Windows Game DVR",
    "opt.desc.gamedvr": "Stops the hidden screen recorder that steals GPU frames.",
    "opt.items.gamebar": "Disable Xbox Game Bar",
    "opt.desc.gamebar": "Removes overlay hooks that add frame and input latency.",
    "opt.items.notifications": "Silence toast notifications",
    "opt.desc.notifications": "Prevents popup interrupts from stealing focus.",
    "opt.items.power": "High Performance power plan",
    "opt.desc.power": "Removes power-saving caps on CPU and GPU clocks.",
    "opt.items.services": "Pause background services",
    "opt.desc.services": "SysMain, Windows Search and telemetry paused (restored later).",
    "opt.items.killapps": "Close background apps on boost",
    "opt.desc.killapps": "Closes the apps selected in Settings before boosting.",

    "set.title": "SETTINGS",
    "set.repo": "REPOSITORY",
    "set.repo.hint": "The app and the installer fetch code and commands from this GitHub repository.",
    "set.repo.name": "Repository (owner/name)",
    "set.repo.branch": "Branch",
    "set.repo.fetch": "FETCH LATEST",
    "set.repo.fetching": "FETCHING",
    "set.repo.ok": "Updated",
    "set.repo.fail": "Failed",
    "set.lang": "LANGUAGE",
    "set.lang.en": "English",
    "set.lang.nl": "Nederlands",
    "set.general": "GENERAL",
    "set.startup": "Start with Windows",
    "set.apps": "BACKGROUND APPS",
    "set.apps.hint": "Selected apps are closed when the boost runs (Optimizer: close background apps).",
    "set.apps.add": "Add process name...",
    "set.reset": "FACTORY RESET",
    "set.reset.done": "Settings restored to defaults",

    "log.title": "ACTIVITY LOG",
    "log.clear": "CLEAR",
    "log.save": "SAVE",
    "log.saved": "Log saved",
    "log.admin_hint": "Not running as admin - advanced items are locked.",
    "log.autoprio": "Auto game mode: Roblox priority set to High",
    "log.started": "Application started",
    "log.reverted": "Defaults restored",
    "log.boost.start": "Boost started",
    "log.apps.closed": "Closed apps: {n}",

    "modal.boost": "BOOST COMPLETE",
    "modal.before": "Before",
    "modal.after": "After",
    "modal.delta": "Improvement",
    "modal.ok": "OK",
    "modal.updated": "REPOSITORY UPDATED",
    "modal.updated.hint": "Restart the app or run the installer to apply the new version.",
    "common.na": "n/a",
}

_NL = {
    "titlebar.app": "NEON FPS BOOSTER",
    "titlebar.tagline": "PROFESSIONELE EDITIE",

    "nav.dashboard": "Dashboard",
    "nav.optimizer": "Optimizer",
    "nav.settings": "Instellingen",
    "nav.log": "Logboek",

    "dash.status": "SYSTEEMSTATUS",
    "dash.fps": "FPS INDEX",
    "dash.fps.sub": "live micro-benchmark",
    "dash.cpu": "CPU",
    "dash.ram": "RAM",
    "dash.gpu": "GPU",
    "dash.load": "belasting",
    "dash.boost": "NU OPTIMALISEREN",
    "dash.boost.sub": "1-klik prestatieboost",
    "dash.boosting": "BOOSTEN",
    "dash.bench": "BENCHMARK DRAAIEN",
    "dash.bench.run": "BENCHMARK DRAAIT",
    "dash.last": "laatste volledige benchmark",
    "dash.game": "SPELPROCES",
    "dash.game.running": "Roblox gedetecteerd",
    "dash.game.idle": "Roblox draait niet",
    "dash.game.name": "Naam",
    "dash.game.prio": "Prioriteit",
    "dash.game.cpu": "CPU",
    "dash.game.pid": "PID",
    "dash.game.apply": "ZET NU OP HOOG",
    "dash.history": "PRESTATIEGESCHIEDENIS",
    "dash.history.sub": "prestatie-index - live",

    "opt.title": "OPTIMIZER",
    "opt.apply": "ALLES TOEPASSEN",
    "opt.revert": "STANDAARD HERSTELLEN",
    "opt.applied": "TOEGEPASTD",
    "opt.off": "UIT",
    "opt.on": "AAN",
    "opt.admin": "ADMIN",
    "opt.error": "FOUT",
    "opt.sec.game": "SPEELMODUS",
    "opt.sec.win": "WINDOWS",
    "opt.sec.adv": "GEVORDERD",
    "opt.admin.hint": "Geavanceerde items vereisen administrator-rechten.",
    "opt.items.priority": "Roblox prioriteit op HOOG",
    "opt.desc.priority": "Zet het spelproces boven achtergrondtaken.",
    "opt.items.autoprio": "Automatische gamemodus",
    "opt.desc.autoprio": "Houdt Roblox op HOOG prioriteit terwijl het draait.",
    "opt.items.gamedvr": "Windows Game DVR uitschakelen",
    "opt.desc.gamedvr": "Stopt de verborgen schermopnemer die GPU-frames wegneemt.",
    "opt.items.gamebar": "Xbox Game Bar uitschakelen",
    "opt.desc.gamebar": "Haalt overlay-hooks weg die frame- en invoerlatentie toevoegen.",
    "opt.items.notifications": "Pop-up meldingen onderdrukken",
    "opt.desc.notifications": "Voorkomt dat pop-ups de focus stjelen.",
    "opt.items.power": "Stroomplan: High Performance",
    "opt.desc.power": "Verwijdert besparingslimieten op CPU- en GPU-klokken.",
    "opt.items.services": "Achtergrondservices pauzeren",
    "opt.desc.services": "SysMain, Windows Search en telemetry gepauzeerd (later hersteld).",
    "opt.items.killapps": "Sluit achtergrond-apps bij boost",
    "opt.desc.killapps": "Sluit de apps uit Instellingen voor de boost.",

    "set.title": "INSTELLINGEN",
    "set.repo": "REPOSITORY",
    "set.repo.hint": "De app en de installer halen code en opdrachten op uit deze GitHub-repository.",
    "set.repo.name": "Repository (eigenaar/naam)",
    "set.repo.branch": "Branch",
    "set.repo.fetch": "HAAL LAATSTE OP",
    "set.repo.fetching": "OPHALEN",
    "set.repo.ok": "Bijgewerkt",
    "set.repo.fail": "Mislukt",
    "set.lang": "TAAL",
    "set.lang.en": "English",
    "set.lang.nl": "Nederlands",
    "set.general": "ALGEMEEN",
    "set.startup": "Start met Windows",
    "set.apps": "ACHTERGROND-APPS",
    "set.apps.hint": "Geselecteerde apps worden gesloten bij de boost (Optimizer: sluit achtergrond-apps).",
    "set.apps.add": "Procesnaam toevoegen...",
    "set.reset": "HERSTEL STANDAARD",
    "set.reset.done": "Instellingen hersteld",

    "log.title": "ACTIELOGBOEK",
    "log.clear": "WISSEN",
    "log.save": "OPSLAAN",
    "log.saved": "Logboek opgeslagen",
    "log.admin_hint": "Niet als admin - geavanceerde items zijn geblokkeerd.",
    "log.autoprio": "Automatische gamemodus: Roblox prioriteit op Hoog gezet",
    "log.started": "Applicatie gestart",
    "log.reverted": "Standaardinstellingen hersteld",
    "log.boost.start": "Boost gestart",
    "log.apps.closed": "Gesloten apps: {n}",

    "modal.boost": "BOOST VOLTOOID",
    "modal.before": "Voor",
    "modal.after": "Na",
    "modal.delta": "Verbetering",
    "modal.ok": "OK",
    "modal.updated": "REPOSITORY BIJGEWERKT",
    "modal.updated.hint": "Herstart de app of draai de installer om de nieuwe versie toe te passen.",
    "common.na": "n/b",
}

_LANGS = {"en": _EN, "nl": _NL}
_current = "en"


def detect():
    """Detect system language (Dutch -> nl, everything else -> en)."""
    try:
        loc = (locale.getdefaultlocale()[0] or "").lower()
        if loc.startswith("nl"):
            return "nl"
    except Exception:
        pass
    return "en"


def set_lang(lang):
    global _current
    _current = lang if lang in _LANGS else "en"


def lang():
    return _current


def t(key):
    v = _LANGS[_current].get(key)
    if v is None:
        v = _EN.get(key, key)
    return v


def tr(key, **kw):
    s = t(key)
    if kw:
        try:
            s = s.format(**kw)
        except Exception:
            pass
    return s
