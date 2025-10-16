from pathlib import Path
import src.gui.state.root as root
from src.gui.utils.config_loader import get_setting
from src.gui.state.error import Error
import customtkinter
import src.gui.utils.logger as log


def load():
    try:
        folder = Path("./src/assets/styles_global")
        for file in folder.glob("*.json"):
            style_code = file.stem
            if style_code not in root.all_styles:
                root.all_styles[file.stem] = file.__str__()
            else:
                print(Error.STYLE_LOADING.value)
        default_style: str = get_setting("color_theme")
        set_style(default_style)
    except Exception:
        log.log.write(text=Error.STYLE_LOADING.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)


def set_style(name: str):
    if name in root.all_styles:
        if root.all_styles[name] is None:
            customtkinter.set_default_color_theme(name)
        else:
            customtkinter.set_default_color_theme(root.all_styles[name])  # type: ignore
    else:
        log.log.write(text=Error.STYLE_NOT_EXIST.value, tag="WARNING", modulename=Path(__file__).stem)
