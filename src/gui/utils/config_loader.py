import json
from ..state.root import settings
from ..utils.lang_loader import get


def load():
    global settings
    with open("./src/assets/settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
    if settings is None:
        raise Exception("Settings could not be loaded!")


def get_setting(key: str):
    if settings is None:
        raise Exception("Settings could not be loaded!")
    if key in settings:
        return settings[key]
    return None
