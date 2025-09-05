from typing import Callable
import customtkinter

from src.gui.layout.filter_window import FilterWindow
from src.gui.state.project_file_type import Filter_Type
from src.gui.utils.config_loader import get_setting
from src.gui.state import root


class FilterEntryFrame(customtkinter.CTkFrame):

    updater: Callable
    id: str | None = None
    filter: Filter_Type | None = None
    name_label: customtkinter.CTkLabel | None = None
    size_label: customtkinter.CTkLabel | None = None
    type_label: customtkinter.CTkLabel | None = None
    edit_button: customtkinter.CTkButton | None = None
    delete_button: customtkinter.CTkButton | None = None

    filter_window: FilterWindow | None = None

    def __init__(self, master, filter, id: str, *args, **kwargs) -> None:
        self._layout_settings = get_setting("components")["filter_entry_frame"]
        super().__init__(master=master, border_width=0, corner_radius=0, *args, **kwargs)
        self.filter = filter
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, minsize=50)
        self.grid_columnconfigure(3, minsize=10)

        self.grid_rowconfigure(0, weight=1)
        self.id = id
        if type(self.filter) is dict:
            self.name_label = customtkinter.CTkLabel(master=self, text=self.filter["name"], corner_radius=0)
            self.type_label = customtkinter.CTkLabel(master=self, text=root.current_lang.get(self.filter["settings"]["type"]).get(), corner_radius=0)
            self.type_label.grid(row=0, column=1, sticky="nswe", pady=self._layout_settings["padding"], padx=0)
            self.size_label = customtkinter.CTkLabel(master=self, text=str(self.filter["settings"]["size"]), corner_radius=0)
            self.size_label.grid(row=0, column=2, sticky="nswe", pady=self._layout_settings["padding"], padx=0)
        elif type(self.filter) is str:
            self.name_label = customtkinter.CTkLabel(master=self, text=self.filter, corner_radius=0)
        else:
            self.name_label = customtkinter.CTkLabel(master=self, textvariable=root.current_lang.get("components_filter_entry_frame_name_none"), corner_radius=0)
        self.name_label.grid(row=0, column=0, sticky="nswe", pady=self._layout_settings["padding"], padx=[self._layout_settings["padding"], 0])

        self.delete_button = customtkinter.CTkButton(master=self, textvariable=root.current_lang.get("components_filter_entry_frame_button_delete"), image=root.all_icons["delete"], compound="left", corner_radius=0)
        self.delete_button.grid(row=0, column=4, sticky="nswe", pady=self._layout_settings["padding"], padx=0)

        self.edit_button = customtkinter.CTkButton(master=self, textvariable=root.current_lang.get("components_filter_entry_frame_button_edit"), image=root.all_icons["edit"], command=self.open_filter_window, corner_radius=0)
        self.edit_button.grid(row=0, column=5, sticky="nswe", pady=self._layout_settings["padding"], padx=[0, self._layout_settings["padding"]])

    def set_updater(self, updater: Callable):
        self.updater = updater

    def update(self, data: Filter_Type):
        self.filter = data
        assert self.type_label is not None and self.size_label is not None and self.name_label is not None
        self.name_label.configure(text=self.filter["name"])
        self.size_label.configure(text=str(self.filter["settings"]["size"]))
        self.type_label.configure(text=root.current_lang.get(self.filter["settings"]["type"]).get())
        self.updater(self, self.filter)

    def delete(self):
        pass

    def get_info(self) -> Filter_Type | str | None:
        return self.filter

    def open_filter_window(self):
        if self.filter_window is not None and self.filter_window.winfo_exists():
            self.filter_window.focus()
        else:
            if self.filter is not None:
                self.filter_window = FilterWindow(master=self, filter=self.filter, updater=self.update)
