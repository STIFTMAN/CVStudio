from pathlib import Path
import src.gui.state.root as root
from src.gui.utils.config_loader import get_setting
from ..state.error import Error
import customtkinter


def load():
    folder = Path("./src/assets/styles_global")
    for file in folder.glob("*.json"):
        style_code = file.stem
        if style_code not in root.all_styles:
            root.all_styles[file.stem] = file.__str__()
        else:
            print(Error.STYLE_LOADING.value)
    default_style: str = get_setting("color_theme")
    set_style(default_style)


def set_style(name: str):
    if name in root.all_styles:
        if root.all_styles[name] is None:
            customtkinter.set_default_color_theme(name)
        else:
            customtkinter.set_default_color_theme(root.all_styles[name])  # type: ignore
    else:
        print(Error.STYLE_NOT_EXIST.value)
