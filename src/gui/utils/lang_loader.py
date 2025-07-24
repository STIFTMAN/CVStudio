import json
from pathlib import Path
from ..state.root import lang, current_lang
from ..state.error import Error
from ..utils.config_loader import get_setting


def load():
    global lang
    folder = Path("./src/assets/lang")
    for file in folder.glob("*.json"):
        lang_code = file.stem
        with open(file, "r", encoding="utf-8") as f:
            lang[lang_code] = json.load(f)
    default_lang_key_code: str = get_setting("default_lang")
    default_lang_size: int = len(lang[default_lang_key_code])
    for lang_code in lang:
        if lang_code == default_lang_key_code:
            continue
        if len(lang[lang_code]) != default_lang_size:
            raise Exception(Error.LANG_INVALID_SIZE.value)
        for key in lang[default_lang_key_code]:
            if key not in lang[lang_code]:
                raise Exception(Error.LANG_TRANSLATION_MISSING.value, lang_code, key)
    current_lang_code: str = get_setting("lang")
    if current_lang_code in lang:
        current_lang.change(lang[current_lang_code])
    else:
        raise Exception(Error.LANG_KEY_NOT_EXIST.value, current_lang_code)
