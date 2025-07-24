import json
from pathlib import Path
from ..state.root import lang
from ..utils.config_loader import get_setting


def load():
    global lang
    folder = Path("./src/assets/lang")
    for file in folder.glob("*.json"):
        lang_code = file.stem
        with open(file, "r", encoding="utf-8") as f:
            lang[lang_code] = json.load(f)
    print(lang)


def get(key: str):
    lang_key_code: str = get_setting("lang")
    return lang[lang_key_code][key]
