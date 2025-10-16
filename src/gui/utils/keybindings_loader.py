import json
import src.gui.state.root as root
import src.gui.utils.logger as log
from src.gui.state.error import Error
from pathlib import Path


def load():
    with open("./src/assets/keybindings.json", "r", encoding="utf-8") as f:
        root.all_keybindings = json.load(f)
    if root.all_keybindings is None:
        log.log.write(text=Error.KEYBINDINGS_LOADING.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)