import json
from ..state.root import settings
from ..state.error import Error


def load():
    global settings
    with open("./src/assets/settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
    if settings is None:
        raise Exception(Error.SETTINGS_LOADING.value)


def get_setting(key: str):
    if settings is None:
        raise Exception(Error.SETTINGS_LOADING.value)
    if key in settings:
        return settings[key]
    raise Exception(Error.SETTINGS_KEY_NOT_EXIST.value)
