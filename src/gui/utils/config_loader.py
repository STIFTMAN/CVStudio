import json
from pathlib import Path
from typing import Any
from PIL import Image
import customtkinter
import src.gui.state.root as root
from ..state.error import Error
from .version import get_git_version


def load():
    with open("./src/assets/settings.json", "r", encoding="utf-8") as f:
        root.settings = json.load(f)
    if root.settings is None:
        raise Exception(Error.SETTINGS_LOADING.value)
    root.version = "v" + get_setting("version") + "-" + get_git_version()
    folder = Path("./src/assets/img")
    for file in folder.glob("*.png"):
        name = file.stem
        root.all_icons[name] = customtkinter.CTkImage(light_image=Image.open(file))
    customtkinter.set_appearance_mode(get_setting("darkmode"))


def get_setting(key: str) -> Any:
    if root.settings is None:
        raise Exception(Error.SETTINGS_LOADING.value)
    if key in root.settings:
        return root.settings[key]
    raise Exception(Error.SETTINGS_KEY_NOT_EXIST.value)


def save_settings() -> None:
    if root.settings is not None:
        with open("./src/assets/settings.json", "w", encoding="utf-8") as f:
            json.dump(root.settings, f, indent=4)
