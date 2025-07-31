import json
import src.gui.state.root as root
from ..state.error import Error
from .version import get_git_version


def load():
    with open("./src/assets/settings.json", "r", encoding="utf-8") as f:
        root.settings = json.load(f)
    if root.settings is None:
        raise Exception(Error.SETTINGS_LOADING.value)
    root.version = "v" + get_setting("version") + "-" + get_git_version()


def get_setting(key: str):
    if root.settings is None:
        raise Exception(Error.SETTINGS_LOADING.value)
    if key in root.settings:
        return root.settings[key]
    raise Exception(Error.SETTINGS_KEY_NOT_EXIST.value)


def save_settings():
    if root.settings is not None:
        with open("./src/assets/settings.json", "w", encoding="utf-8") as f:
            json.dump(root.settings, f, indent=4)
