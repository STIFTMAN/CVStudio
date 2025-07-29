import json
import src.gui.state.root as root
from ..state.error import Error


def load():
    with open("./src/assets/keybindings.json", "r", encoding="utf-8") as f:
        root.all_keybindings = json.load(f)
    if root.all_keybindings is None:
        raise Exception(Error.KEYBINDINGS_LOADING.value)