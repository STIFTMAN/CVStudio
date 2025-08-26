from typing import Callable
import customtkinter

from src.gui.layout.filter_window import FilterWindow
from src.gui.state.project_file_type import Filter_Type


class FilterEntryFrame(customtkinter.CTkFrame):

    updater: Callable

    filter: Filter_Type | str | None = None

    name_label: customtkinter.CTkLabel | None = None
    size_label: customtkinter.CTkLabel | None = None
    type_label: customtkinter.CTkLabel | None = None
    edit_button: customtkinter.CTkButton | None = None
    delete_button: customtkinter.CTkButton | None = None

    filter_window: FilterWindow | None = None

    def __init__(self, master, filter, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self.filter = filter
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if type(self.filter) is dict:
            self.name_label = customtkinter.CTkLabel(master=self, text=self.filter["name"])
            self.type_label = customtkinter.CTkLabel(master=self, text=self.filter["settings"]["type"])
            self.type_label.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")
            self.size_label = customtkinter.CTkLabel(master=self, text=str(self.filter["settings"]["size"]))
            self.size_label.grid(row=0, column=2, padx=10, pady=10, sticky="nswe")
        elif type(self.filter) is str:
            self.name_label = customtkinter.CTkLabel(master=self, text=self.filter)
        else:
            self.name_label = customtkinter.CTkLabel(master=self, text="None")
        self.name_label.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")

        self.delete_button = customtkinter.CTkButton(master=self, text="Delete")
        self.delete_button.grid(row=0, column=3, padx=10, pady=10, sticky="nswe")

        self.edit_button = customtkinter.CTkButton(master=self, text="Edit", command=self.open_filter_window)
        self.edit_button.grid(row=0, column=4, padx=10, pady=10, sticky="nswe")

    def set_updater(self, updater: Callable):
        self.updater = updater

    def update(self, data: Filter_Type):
        self.filter = data
        assert type(self.filter) is dict
        self.updater(self, self.filter)

    def delete(self):
        pass

    def get_info(self) -> Filter_Type | str | None:
        return self.filter

    def open_filter_window(self):
        if self.filter_window is not None and self.filter_window.winfo_exists():
            self.filter_window.focus()
        else:
            self.filter_window = FilterWindow(master=self, filter=self.filter, updater=self.update)
