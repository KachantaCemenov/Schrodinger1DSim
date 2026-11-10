import os
import shutil
from pathlib import Path
from uuid import uuid4


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
        root = RECOVERY ROOT.resolve()
        target = self.path.resolve()

        if target.parent != root or target.name != self.path.name:
            raise ValueError("Incorrect benchmark recovery folder.")

        if target.exists():
            shutil.rmtree(target) #permanently delete the directory