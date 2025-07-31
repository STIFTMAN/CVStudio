from typing import TypedDict


class Settings_Type(TypedDict):
    lang: str
    darkmode: bool
    color_theme: str
    window_size: dict[str, tuple[int, int]]
    components: dict
    help_url: str
    version: str
    name: str
    license: str
