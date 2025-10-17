import customtkinter
from src.gui.state.project_file_type import Project_File_Type, Action_Type
from src.gui.utils.project import Project
from ..utils.string_list import StringList
from .settings_type import Settings_Type


settings: None | Settings_Type = None
lang: dict[str, dict[str, str]] = {}
current_lang: StringList = StringList()
all_lang: dict[str, str] = {}
all_styles: dict[str, str | None] = {"blue": None,
                                     "dark-blue": None,
                                     "green": None}
all_filter_types: list[str] = ["smoothing", "edge_detection", "median", "minimum", "maximum", "25%_quantile", "75%_quantile"]
all_filters: dict[str, Action_Type] = {}
all_keybindings: dict[str, str] | None = None
version: str = "unknown"
all_projects: dict[str, Project_File_Type] = {}
current_project: Project = Project()
all_icons: dict[str, customtkinter.CTkImage] = {}
status: customtkinter.StringVar | None = None
status_details: customtkinter.StringVar | None = None
status_test: customtkinter.StringVar | None = None
