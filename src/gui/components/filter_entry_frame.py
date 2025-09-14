from typing import Callable
import customtkinter

from src.gui.layout.filter_window import FilterWindow
from src.gui.state.project_file_type import Action_Type, Filter_Type
from src.gui.utils.config_loader import get_setting
from src.gui.state import root


class FilterEntryFrame(customtkinter.CTkFrame):

    updater: Callable
    deleter: Callable
    id: str | None = None
    data: Action_Type | None = None
    id_label: customtkinter.CTkLabel | None = None
    name_label: customtkinter.CTkLabel | None = None
    size_label: customtkinter.CTkLabel | None = None
    action_label: customtkinter.CTkLabel | None = None
    type_label: customtkinter.CTkLabel | None = None
    edit_button: customtkinter.CTkButton | None = None
    delete_button: customtkinter.CTkButton | None = None

    filter_window: FilterWindow | None = None

    def __init__(self, master, action: Action_Type | None, id: str, *args, **kwargs) -> None:
        self._layout_settings = get_setting("components")["filter_entry_frame"]
        super().__init__(master=master, border_width=0, corner_radius=0, *args, **kwargs)
        self.data = action
        self.grid_columnconfigure(0, minsize=100)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, minsize=80)
        self.grid_columnconfigure(3, minsize=80)
        self.grid_columnconfigure(4, minsize=30)
        self.grid_columnconfigure(5, minsize=30)

        self.grid_rowconfigure(0, weight=1)
        self.id = id
        if self.data is not None:
            self.id_label = customtkinter.CTkLabel(master=self, text=id[0:8], corner_radius=0)
            self.id_label.grid(row=0, column=0, sticky="nswe", pady=self._layout_settings["padding"], padx=[self._layout_settings["padding"], 0])
            if isinstance(self.data["data"], str):
                self.name_label = customtkinter.CTkLabel(master=self, text=self.data["data"], corner_radius=0, anchor="w")
                self.action_label = customtkinter.CTkLabel(master=self, text=root.current_lang.get(self.data["type"]).get(), corner_radius=0)
                self.action_label.grid(row=0, column=2, sticky="nswe", pady=self._layout_settings["padding"], padx=[self._layout_settings["padding"], 0])
            else:
                self.name_label = customtkinter.CTkLabel(master=self, text=self.data["data"]["name"], corner_radius=0, anchor="w")
                self.action_label = customtkinter.CTkLabel(master=self, text=root.current_lang.get(self.data["type"]).get(), corner_radius=0)
                self.action_label.grid(row=0, column=2, sticky="nswe", pady=self._layout_settings["padding"], padx=[self._layout_settings["padding"], 0])
                self.type_label = customtkinter.CTkLabel(master=self, text=root.current_lang.get(self.data["data"]["settings"]["type"]).get(), corner_radius=0)
                self.type_label.grid(row=0, column=3, sticky="nswe", pady=self._layout_settings["padding"], padx=[self._layout_settings["padding"], 0])
                self.size_label = customtkinter.CTkLabel(master=self, text=str(self.data["data"]["settings"]["size"]), corner_radius=0)
                self.size_label.grid(row=0, column=4, sticky="nswe", pady=self._layout_settings["padding"], padx=[self._layout_settings["padding"], 0])
        else:
            self.name_label = customtkinter.CTkLabel(master=self, textvariable=root.current_lang.get("components_filter_entry_frame_name_none"), anchor="left", corner_radius=0)
        self.name_label.grid(row=0, column=1, sticky="nswe", pady=self._layout_settings["padding"], padx=[self._layout_settings["padding"], 0])

        self.delete_button = customtkinter.CTkButton(master=self, textvariable=root.current_lang.get("components_filter_entry_frame_button_delete"), image=root.all_icons["delete"], compound="left", corner_radius=0, command=self.delete)
        self.delete_button.grid(row=0, column=6, sticky="nswe", pady=self._layout_settings["padding"], padx=0)

        if self.data is not None:
            if isinstance(self.data["data"], dict):
                self.edit_button = customtkinter.CTkButton(master=self, textvariable=root.current_lang.get("components_filter_entry_frame_button_edit"), image=root.all_icons["edit"], command=self.open_filter_window, corner_radius=0)
                self.edit_button.grid(row=0, column=7, sticky="nswe", pady=self._layout_settings["padding"], padx=[0, self._layout_settings["padding"]])

    def get_update(self, data: Filter_Type):
        if self.id is not None and self.data is not None:
            self.data["data"] = data
            if isinstance(self.data["data"], dict):
                assert self.type_label is not None and self.size_label is not None and self.name_label is not None
                self.name_label.configure(text=self.data["data"]["name"])
                self.size_label.configure(text=str(self.data["data"]["settings"]["size"]))
                self.type_label.configure(text=root.current_lang.get(self.data["data"]["settings"]["type"]).get())

    def set_updater(self, updater: Callable):
        self.updater = updater

    def delete(self):
        if self.filter_window is not None:
            self.filter_window.destroy()
            self.filter_window = None
        self.deleter(self)

    def update(self, data: Filter_Type):
        assert self.data is not None
        self.data["data"] = data
        assert self.type_label is not None and self.size_label is not None and self.name_label is not None
        self.name_label.configure(text=self.data["data"]["name"])
        self.size_label.configure(text=str(self.data["data"]["settings"]["size"]))
        self.type_label.configure(text=root.current_lang.get(self.data["data"]["settings"]["type"]).get())
        self.updater(self, self.data["data"])

    def set_deleter(self, deleter: Callable):
        self.deleter = deleter

    def open_filter_window(self):
        if self.filter_window is not None and self.filter_window.winfo_exists():
            self.filter_window.focus()
        else:
            if self.data is not None:
                if isinstance(self.data["data"], dict):
                    self.filter_window = FilterWindow(master=self, filter=self.data["data"], updater=self.update)
