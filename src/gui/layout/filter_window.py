from typing import Callable
import customtkinter

from src.gui.state.project_file_type import Filter_Type
from src.gui.utils.config_loader import get_setting


class FilterWindow(customtkinter.CTkToplevel):

    grid_container: customtkinter.CTkFrame | None = None
    settings_container: customtkinter.CTkFrame | None = None

    updater: Callable
    filter: Filter_Type | None = None

    def __init__(self, master, filter, updater: Callable, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.iconbitmap("src/assets/favicon.ico")
        filter_window_size = get_setting("window_size")["filter"]
        screen_coords = (int((master.winfo_screenwidth() - filter_window_size[0]) / 2), int((master.winfo_screenheight() - filter_window_size[1]) / 2))
        self.geometry(f"{filter_window_size[0]}x{filter_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.minsize(filter_window_size[0], filter_window_size[1])
        self.after(100, self.focus)
        self.filter = filter
        self.updater = updater

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build_grid_container()
        self.build_settings_container()

    def clear_grid_container(self):
        pass

    def build_grid_container(self):
        self.grid_container = customtkinter.CTkFrame(master=self)
        self.grid_container.grid(row=0, column=0, sticky="nswe", padx=[10, 10], pady=[10, 10])

    def build_settings_container(self):
        self.settings_container = customtkinter.CTkFrame(master=self)
        self.settings_container.grid(row=0, column=1, sticky="ns", padx=[0, 10], pady=[10, 10])

        apply_button: customtkinter.CTkButton = customtkinter.CTkButton(master=self.settings_container, text="Apply Changes", command=self.update)
        apply_button.grid(row=0, column=0, padx=[10, 10], pady=[10, 10])

    def update(self):
        self.updater(self.filter)
