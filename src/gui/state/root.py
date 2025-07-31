from ..utils.string_list import StringList
from .settings_type import Settings_Type


settings: None | Settings_Type = None
lang: dict[str, dict[str, str]] = {}
current_lang: StringList = StringList()
all_lang: dict[str, str] = {}
all_styles: dict[str, str | None] = {"blue": None,
                                     "dark-blue": None,
                                     "green": None}
all_keybindings: dict[str, str] | None = None
version: str = "unknown"
