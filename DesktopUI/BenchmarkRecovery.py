import os
import shutil
from pathlib import Path
from uuid import uuid4
import re
import msvcrt

"""
This script is intended to save the checkpoint of a running benchmark so that when the app is forced close,
The saved running benchmark can be read the next time the app is opened in order for it to be resumed
"""

#Path.home() -> WindowsPath('C:/Users/Username')
RECOVERY_ROOT = Path.home() / "Schrodinger1DSim" / "UnfinishedRuns"

class BenchmarkWorkingDirectory:
    #Persistent until explicitly saved or discarded

    def __init__(self):
        RECOVERY_ROOT.mkdir(parents = True, exist_ok = True)

        self.path = RECOVERY_ROOT / f"run_{uuid4().hex}"
        self.path.mkdir()
        self.name = str(self.path)

    def cleanup(self):
        root = RECOVERY_ROOT.resolve()
        target = self.path.resolve()

        if target.parent != root or target.name != self.path.name:
            raise ValueError("Incorrect benchmark recovery folder.")

        if target.exists():
            shutil.rmtree(target) #permanently delete the directory


def CheckRecoveryFolder(folder):
    root = RECOVERY_ROOT.resolve()
    folder = Path(folder).resolve()

    if folder.parent != root or re.fullmatch(r"run_[0-9a-f]{32}", folder.name) is None:
        raise ValueError("Not an application recovery folder.")

    return folder


def IsRecoveryFolder(folder):
    try:
        CheckRecoveryFolder(folder)
        return True
    except (OSError, ValueError):
        return False


def ListRecoveryFolders():
    if not RECOVERY_ROOT.exists():
        return []

    folders = []
    for c in RECOVERY_ROOT.iterdir():
        if c.is_dir() and IsRecoveryFolder(c):
            folders.append(c)

    return sorted(folders, key=lambda folder: folder.name)


def DeleteRecoveryFolder(folder):
    folder = CheckRecoveryFolder(folder)
    if folder.exists():
        shutil.rmtree(folder)


def AcquireRecoveryLock():
    #Prevent another app instance from managing active recovery folders.
    RECOVERY_ROOT.mkdir(parents=True, exist_ok=True)
    handle = (RECOVERY_ROOT / ".application.lock").open("a+b")

    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        handle.close()
        raise RuntimeError("Another simulator instance is already using benchmark recovery.") from None

    return handle