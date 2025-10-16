from pathlib import Path
import os
import sys
import subprocess


def open_app(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch(exist_ok=True)

    if sys.platform.startswith("win"):
        os.startfile(p)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(p)])
    else:
        subprocess.Popen(["xdg-open", str(p)])
