from enum import Enum


class Error(Enum):
    SETTINGS_LOADING = "Settings could not be loaded!"
    SETTINGS_KEY_NOT_EXIST = "Settings key does not exists!"
    LANG_TRANSLATION_MISSING = "Translation missing!"
    LANG_KEY_NOT_EXIST = "Translation key does not exist!"
    LANG_INVALID_SIZE = "Length of translation file is different than default lang file!"
    LANG_NOT_EXIST = "Language does not exist!"
    STYLE_LOADING = "Not allowed to  override default theme ('blue', 'dark-blue', 'green'). Chose different file name"
    STYLE_NOT_EXIST = "Style does not exist!"
    KEYBINDINGS_LOADING = "Keybindings could not be loaded!"
    INVALID_PROJECT_FILE = "Project file is invalid!"
    CREATE_PROJECT = "Could not create project file!"
