import json
from pathlib import Path
import src.gui.state.root as root
from ..state.error import Error
from ..utils.config_loader import get_setting
import logging


def load():
    folder = Path("./src/assets/lang")
    for file in folder.glob("*.json"):
        lang_code = file.stem
        with open(file, "r", encoding="utf-8") as f:
            root.lang[lang_code] = json.load(f)
    default_lang_key_code: str = get_setting("default_lang")
    default_lang_size: int = len(root.lang[default_lang_key_code])
    for lang_code in root.lang:
        if lang_code == default_lang_key_code:
            continue
        if len(root.lang[lang_code]) != default_lang_size:
            raise Exception(Error.LANG_INVALID_SIZE.value)
        for key in root.lang[default_lang_key_code]:
            if key not in root.lang[lang_code]:
                raise Exception(Error.LANG_TRANSLATION_MISSING.value, lang_code, key)
    current_lang_code: str = get_setting("lang")
    if current_lang_code in root.lang:
        root.current_lang.change(root.lang[current_lang_code])
    else:
        raise Exception(Error.LANG_KEY_NOT_EXIST.value, current_lang_code)
    root.all_lang = get_translation_from_all_lang("language_package_name")


def get_all_lang_code() -> list[str]:
    return [key for key in root.lang]


def get_translation_from_all_lang(key: str) -> dict[str, str]:
    tmp_dict: dict[str, str] = {}
    for lang_code in get_all_lang_code():
        tmp_dict[lang_code] = root.lang[lang_code][key]
    return tmp_dict


def change_lang(lang_code: str):
    if lang_code not in get_all_lang_code():
        logging.basicConfig(level=logging.WARNING)
        logging.warning(Error.LANG_NOT_EXIST.value)
        return
    root.current_lang.change(root.lang[lang_code])
