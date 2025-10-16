import subprocess
import src.gui.utils.logger as log
from src.gui.state.error import Error
from pathlib import Path


def get_git_version():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        log.log.write(text=Error.VERSION_GIT_VERSION.value, tag="WARNING", modulename=Path(__file__).stem)
        return "unknown"
