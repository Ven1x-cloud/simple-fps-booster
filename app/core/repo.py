"""Fetch application source from a GitHub repository.

git clone is tried first; a codeload tarball download is the fallback.
Used by the in-app "fetch latest" update and mirrored by installer.py
(which must stay self-contained, so it keeps its own copy of this logic).
"""
import io
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

DEFAULT_REPO = "Ven1x-cloud/simple-fps-booster"
DEFAULT_BRANCH = "main"


class RepoError(Exception):
    pass


def parse_repo(spec):
    """'owner/name', 'https://github.com/owner/name' or git URL -> (owner, name)."""
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
    raise RepoError(f"cannot parse repository '{spec}' - expected owner/name")


def _git_available():
    return bool(shutil.which("git"))


def _clone(owner, repo, branch, dest):
    url = f"https://github.com/{owner}/{repo}.git"
    cmd = ["git", "clone", "--depth", "1", "--branch", branch,
           "--single-branch", url, dest]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RepoError((r.stderr or "git clone failed").strip()[-400:])


def _extract_tarball(data, dest):
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
                    raise RepoError("unsafe path in archive")
            tf.extractall(extracted)
    os.remove(tmp)
    return extracted


def _find_appdir(base):
    for root, dirs, files in os.walk(base):
        if "main.py" in files:
            return root
        if ".git" in dirs:
            dirs.remove(".git")
    return None


def _download(owner, repo, branch, dest):
    url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{branch}"
    req = urllib.request.Request(url, headers={"User-Agent": "NeonFPSBooster"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = resp.read()
    except Exception as e:
        raise RepoError(f"download failed: {e}")
    extracted = _extract_tarball(data, dest)
    found = _find_appdir(extracted)
    if found is None:
        shutil.rmtree(extracted, ignore_errors=True)
        raise RepoError("downloaded archive does not contain main.py")
    if found != extracted:
        # move the inner folder to the requested destination path
        try:
            os.rename(found, dest)
        except OSError:
            shutil.move(found, dest)
        shutil.rmtree(extracted, ignore_errors=True)
    else:
        os.rename(extracted, dest)
    return dest


def fetch_repo(repo_spec=DEFAULT_REPO, branch=DEFAULT_BRANCH, workdir=None,
               force=False):
    """Clone/download the repo. Returns the directory containing main.py."""
    owner, repo = parse_repo(repo_spec)
    branch = (branch or DEFAULT_BRANCH).strip() or DEFAULT_BRANCH
    workdir = workdir or os.path.join(tempfile.gettempdir(), "neon-fps-fetch")
    os.makedirs(workdir, exist_ok=True)
    slug = f"{owner}-{repo}-{branch}".replace("/", "_").replace("\\", "_").replace(" ", "")
    dest = os.path.join(workdir, slug)

    if os.path.isdir(dest) and not force and os.path.isfile(os.path.join(dest, "main.py")):
        return dest
    if os.path.isdir(dest):
        shutil.rmtree(dest, ignore_errors=True)

    if _git_available():
        try:
            _clone(owner, repo, branch, dest)
            appdir = _find_appdir(dest) or dest
            if os.path.isfile(os.path.join(appdir, "main.py")):
                return appdir
        except Exception:
            shutil.rmtree(dest, ignore_errors=True)
        # fall through to tarball

    _download(owner, repo, branch, dest)
    if not os.path.isfile(os.path.join(dest, "main.py")):
        raise RepoError(f"repository {owner}/{repo} has no main.py")
    return dest


def latest_commit(appdir):
    """Short git commit hash if the dir is a git clone, else None."""
    if not os.path.isdir(os.path.join(appdir, ".git")):
        return None
    try:
        r = subprocess.run(["git", "-C", appdir, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def cache_dir():
    d = os.path.join(tempfile.gettempdir(), "neon-fps-fetch")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d
