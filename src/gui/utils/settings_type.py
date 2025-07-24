from typing import TypedDict


class Settings_Type(TypedDict):
    lang: str
    darkmode: bool
    window_size: dict[str, tuple[int, int]]
    components: dict