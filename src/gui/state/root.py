import customtkinter
from ..utils.settings_type import Settings_Type

app: customtkinter.CTk = customtkinter.CTk()
settings: None | Settings_Type = None
lang: dict[str, dict[str, str]] = {}
