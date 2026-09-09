"""Minimal Windows .lnk (shortcut) writer in pure Python - no COM.

Some Windows security setups block COM-based shortcut creation (the
WScript.Shell object used by wscript/powershell), so this module writes
the shortcut file directly using the MS-SHLINK binary format: header,
link-target ID list and the unicode string section (target, working
directory, parameters, icon). That is all a file launcher needs.
"""
import os
import struct
import time

LSF_HAS_LINKTARGETIDLIST = 0x00000002
LSF_HAS_WORKINGDIR = 0x00000004
LSF_HAS_PARAMS = 0x00000008
LSF_HAS_ICONLOCATION = 0x00000010
LSF_NO_UIWARNING = 0x00000200
LSF_UNICODE = 0x00004000

_FILETIME_EPOCH_DIFF = 11644473600  # seconds between 1601 and 1970


def _u16string(text):
    """StringList entry: char count + UTF-16LE data + hazard word."""
    text = text or ""
    return (struct.pack("<H", len(text))
            + text.encode("utf-16-le")
            + struct.pack("<H", 0))


def write_lnk(path, target, args="", workdir="", icon=None):
    """Create a .lnk at `path` pointing at `target`. Returns True on OK."""
    flags = (LSF_HAS_LINKTARGETIDLIST | LSF_HAS_WORKINGDIR
             | LSF_HAS_PARAMS | LSF_UNICODE | LSF_NO_UIWARNING)
    if icon:
        flags |= LSF_HAS_ICONLOCATION
    ft = struct.pack("<Q", int((time.time() + _FILETIME_EPOCH_DIFF)
                               * 10_000_000))
    header = (b"\x4c\x00\x00\x00"
              + struct.pack("<I", flags)
              + struct.pack("<I", 0x20)        # FILE_ATTRIBUTE_NORMAL
              + ft + ft + ft                    # creation/access/write time
              + struct.pack("<I", 0)            # file size
              + struct.pack("<H", 0))           # icon number
    link_id_list = b"\x02\x00"                  # single null-terminated PIDL
    body = (
        _u16string(target)                      # link target
        + _u16string(workdir)                   # working directory
        + struct.pack("<I", 0)                  # working dir attributes
        + _u16string(args)                      # parameters
    )
    if icon:
        body += _u16string(icon) + struct.pack("<H", 0)  # icon path + index
    try:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "wb") as f:
            f.write(header + link_id_list + body)
        return os.path.exists(path)
    except Exception:
        return False


def write_bat(path, target, args=""):
    """Last-resort launcher: a plain .bat (works without any COM, but no
    custom icon is possible for batch files)."""
    try:
        lines = [
            "@echo off",
            "rem Neon FPS Booster launcher",
            f'start "" "{target}" "{args}"',
        ]
        with open(path, "w", encoding="ascii", errors="replace") as f:
            f.write("\r\n".join(lines) + "\r\n")
        return os.path.exists(path)
    except Exception:
        return False
