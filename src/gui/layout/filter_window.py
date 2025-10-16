from typing import Callable
import customtkinter

from src.gui.components.extended_entry import ExtendedEntry
from src.gui.components.filter_grid_cell import FilterGridCell
from src.gui.components.int_entry import IntEntry
from src.gui.state.project_file_type import Filter_Type
from src.gui.utils.config_loader import get_setting
import src.gui.state.root as root


class FilterWindow(customtkinter.CTkToplevel):

    grid_container: customtkinter.CTkFrame | None = None
    settings_container: customtkinter.CTkFrame | None = None
    settings_container_name: ExtendedEntry | None = None
    name_container: customtkinter.CTkFrame | None = None
    name_container_name_label: customtkinter.CTkLabel | None = None
    name_str: customtkinter.StringVar | None = None
    size_container: customtkinter.CTkFrame | None = None
    size_container_name_label: customtkinter.CTkLabel | None = None
    size_container_width_entry: IntEntry | None = None
    size_container_width: customtkinter.IntVar | None = None
    size_container_height: customtkinter.IntVar | None = None
    size_container_height_entry: IntEntry | None = None
    spatial_sampling_rate_container: customtkinter.CTkFrame | None = None
    spatial_sampling_rate_container_name_label: customtkinter.CTkLabel | None = None
    spatial_sampling_rate_container_width_entry: IntEntry | None = None
    spatial_sampling_rate_container_width: customtkinter.IntVar | None = None
    spatial_sampling_rate_container_height: customtkinter.IntVar | None = None
    spatial_sampling_rate_container_height_entry: IntEntry | None = None
    type_container: customtkinter.CTkFrame | None = None
    type_container_name_label: customtkinter.CTkLabel | None = None
    type_container_combobox: customtkinter.CTkOptionMenu | None = None
    type_container_string: customtkinter.StringVar | None = None

    updater: Callable
    filter: Filter_Type | None = None

    type_langs: dict[str, customtkinter.StringVar] = {}

    grid: list[list[FilterGridCell | None]] = []
    grid_size: tuple = (1, 1)

    _layout_settings: dict = {}

    def __init__(self, master, filter: Filter_Type, updater: Callable, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self.title(f"{get_setting('name')} | {root.current_lang.get('filter_window_title').get()} | [{root.current_project.name}]")
        self.after(250, lambda: self.iconbitmap("src/assets/favicon.ico"))
        filter_window_size = get_setting("window_size")["filter"]
        screen_coords = (int((master.winfo_screenwidth() - filter_window_size[0]) / 2), int((master.winfo_screenheight() - filter_window_size[1]) / 2))
        self.geometry(f"{filter_window_size[0]}x{filter_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.minsize(filter_window_size[0], filter_window_size[1])
        self.after(100, self.focus)
        self.filter = filter
        self.updater = updater
        self._layout_settings = get_setting("styles")["filter_window"]
        for key in root.all_filter_types:
            self.type_langs[key] = root.current_lang.get(key)

        if self.filter is not None:
            self.grid_size = (self.filter["settings"]["size"][0], self.filter["settings"]["size"][1])

        self.settings_container_name_str = customtkinter.StringVar(value=self.filter["name"])
        self.size_container_width = customtkinter.IntVar(value=self.grid_size[0])
        self.size_container_height = customtkinter.IntVar(value=self.grid_size[1])

        self.spatial_sampling_rate_container_width = customtkinter.IntVar(value=1)
        self.spatial_sampling_rate_container_height = customtkinter.IntVar(value=1)

        if self.filter["settings"]["type"] not in root.all_filter_types:
            self.type_container_string = customtkinter.StringVar(value=root.current_lang.get(root.all_filter_types[0]).get())
        else:
            self.type_container_string = customtkinter.StringVar(value=root.current_lang.get(self.filter["settings"]["type"]).get())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build_grid_container()
        self.build_settings_container()

        self.settings_container_name_str.trace_add("write", self.update)
        self.size_container_width.trace_add("write", self.update)
        self.size_container_height.trace_add("write", self.update)
        self.spatial_sampling_rate_container_width.trace_add("write", self.update)
        self.spatial_sampling_rate_container_height.trace_add("write", self.update)

    def get_type_langs_key(self, s: str) -> str | None:
        for string in self.type_langs:
            if self.type_langs[string].get() == s:
                return string
        return None

    def clear_grid_container(self):
        if self.grid_container is not None:
            self.grid_container.destroy()
            self.grid_container = None
            for x in range(self.grid_size[0]):
                for y in range(self.grid_size[1]):
                    cell = self.grid[x][y]
                    if cell is not None:
                        cell.destroy()
            self.grid = []

    def build_grid_container(self):
        self.clear_grid_container()
        self.grid_container = customtkinter.CTkFrame(master=self)
        self.grid_container.grid(row=0, column=0, sticky="nswe", padx=self._layout_settings["grid_container"]["padding"][0:2], pady=self._layout_settings["grid_container"]["padding"][2:4])
        if self.filter is not None:
            self.grid = [[None for _ in range(self.grid_size[1])] for _ in range(self.grid_size[0])]
            self.grid_container.grid_columnconfigure(0, weight=1)
            self.grid_container.grid_columnconfigure(self.grid_size[0] + 2, weight=1)
            self.grid_container.grid_rowconfigure(0, weight=1)
            self.grid_container.grid_rowconfigure(self.grid_size[1] + 2, weight=1)
            for x in range(self.grid_size[0]):
                for y in range(self.grid_size[1]):

                    value = 1.0
                    disabled = True
                    if len(self.filter["grid"]) - 1 >= x and len(self.filter["grid"][x]) - 1 >= y:
                        value = self.filter["grid"][x][y]["value"]
                        disabled = self.filter["grid"][x][y]["disabled"]
                    self.grid[x][y] = FilterGridCell(master=self.grid_container, value=value, disabled=disabled)
                    self.grid[x][y].set_updater(self.update_cells)  # type: ignore
                    if self.filter["settings"]["type"] not in ("smoothing", "edge_detection"):
                        self.grid[x][y].toogle_enable_disabled(True)  # type: ignore
                    self.grid[x][y].grid(row=y + 1, column=x + 1, padx=self._layout_settings["grid_container"]["cell"]["padding"][0:2], pady=self._layout_settings["grid_container"]["cell"]["padding"][2:4])  # type: ignore
            if self.filter["settings"]["mutable"] is False:
                for x in range(self.grid_size[0]):
                    for y in range(self.grid_size[1]):
                        cell = self.grid[x][y]
                        if cell is not None:
                            assert cell.entry is not None and cell.switch is not None
                            cell.entry.configure(state="disabled")
                            cell.switch.configure(state="disabled")

    def resize_settings_container(self):
        if self.settings_container is not None:
            req_width = self.settings_container.winfo_reqwidth()
            self.settings_container.configure(width=req_width)

    def build_settings_container(self):
        assert self.filter is not None and self.size_container_width is not None and self.size_container_height is not None
        assert self.spatial_sampling_rate_container_width is not None and self.spatial_sampling_rate_container_height is not None
        assert self.settings_container_name_str is not None

        self.settings_container = customtkinter.CTkFrame(master=self)
        self.settings_container.grid(row=0, column=1, sticky="nswe", padx=self._layout_settings["settings_container"]["padding"][0:2], pady=self._layout_settings["settings_container"]["padding"][2:4])

        self.name_container = customtkinter.CTkFrame(master=self.settings_container, border_width=self._layout_settings["settings_container"]["name_container"]["border_width"])
        self.name_container.grid(row=0, column=0, padx=self._layout_settings["settings_container"]["name_container"]["padding"][0:2], pady=self._layout_settings["settings_container"]["name_container"]["padding"][2:4], sticky="nswe")
        self.name_container.grid_columnconfigure(0, weight=1)

        self.name_container_name_label = customtkinter.CTkLabel(master=self.name_container, textvariable=root.current_lang.get("filter_window_settings_container_name"))
        self.name_container_name_label.grid(row=0, column=0, padx=self._layout_settings["settings_container"]["name_container"]["label"]["padding"][0:2], pady=self._layout_settings["settings_container"]["name_container"]["label"]["padding"][2:4], sticky="nswe")
        id = root.current_project.get_filterid_by_name(self.filter["name"])
        assert id is not None
        self.settings_container_name = ExtendedEntry(master=self.name_container, default_word=root.current_lang.get("filter_window_settings_container_name_default"), id=id, tracker_var=self.settings_container_name_str)
        self.settings_container_name.grid(row=1, column=0, padx=self._layout_settings["settings_container"]["name_container"]["entry"]["padding"][0:2], pady=self._layout_settings["settings_container"]["name_container"]["entry"]["padding"][2:4])

        self.size_container = customtkinter.CTkFrame(master=self.settings_container, border_width=self._layout_settings["settings_container"]["size_container"]["border_width"])
        self.size_container.grid(row=1, column=0, padx=self._layout_settings["settings_container"]["size_container"]["padding"][0:2], pady=self._layout_settings["settings_container"]["size_container"]["padding"][2:4], sticky="nswe")
        self.size_container.grid_columnconfigure(0, weight=1)
        self.size_container.grid_columnconfigure(1, weight=1)

        self.size_container_name_label = customtkinter.CTkLabel(master=self.size_container, textvariable=root.current_lang.get("filter_window_settings_container_size"))
        self.size_container_name_label.grid(row=0, column=0, columnspan=2, padx=self._layout_settings["settings_container"]["size_container"]["label"]["padding"][0:2], pady=self._layout_settings["settings_container"]["size_container"]["label"]["padding"][2:4], sticky="nswe")

        self.size_container_width_entry = IntEntry(master=self.size_container, value=self.filter["settings"]["size"][0], justify="center", width=self._layout_settings["settings_container"]["size_container"]["entry"]["width"])
        self.size_container_width_entry.set_allowed({1, 3, 5, 7, 9})
        self.size_container_width_entry.grid(row=1, column=0, padx=self._layout_settings["settings_container"]["size_container"]["entry"]["padding"][0:2], pady=self._layout_settings["settings_container"]["size_container"]["entry"]["padding"][2:4], sticky="nswe")
        self.size_container_width_entry.set_int_var(self.size_container_width)

        self.size_container_height_entry = IntEntry(master=self.size_container, value=self.filter["settings"]["size"][1], justify="center", width=self._layout_settings["settings_container"]["size_container"]["entry"]["width"])
        self.size_container_height_entry.set_allowed({1, 3, 5, 7, 9})
        self.size_container_height_entry.grid(row=1, column=1, padx=self._layout_settings["settings_container"]["size_container"]["entry"]["padding"][0:2], pady=self._layout_settings["settings_container"]["size_container"]["entry"]["padding"][2:4], sticky="nswe")
        self.size_container_height_entry.set_int_var(self.size_container_height)

        self.spatial_sampling_rate_container = customtkinter.CTkFrame(master=self.settings_container, border_width=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["border_width"])
        self.spatial_sampling_rate_container.grid(row=2, column=0, padx=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["padding"][0:2], pady=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["padding"][2:4], sticky="nswe")
        self.spatial_sampling_rate_container.grid_columnconfigure(0, weight=1)
        self.spatial_sampling_rate_container.grid_columnconfigure(1, weight=1)

        self.spatial_sampling_rate_container_name_label = customtkinter.CTkLabel(master=self.spatial_sampling_rate_container, textvariable=root.current_lang.get("filter_window_settings_container_spatial_sampling_rate"))
        self.spatial_sampling_rate_container_name_label.grid(row=0, column=0, columnspan=2, padx=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["label"]["padding"][0:2], pady=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["label"]["padding"][2:4], sticky="nswe")

        self.spatial_sampling_rate_container_width_entry = IntEntry(master=self.spatial_sampling_rate_container, value=self.filter["settings"]["spatial_sampling_rate"][0], justify="center", width=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["entry"]["width"])
        self.spatial_sampling_rate_container_width_entry.set_value_range((1, None))
        self.spatial_sampling_rate_container_width_entry.grid(row=1, column=0, padx=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["entry"]["padding"][0:2], pady=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["entry"]["padding"][2:4], sticky="nswe")
        self.spatial_sampling_rate_container_width_entry.set_int_var(self.spatial_sampling_rate_container_width)

        self.spatial_sampling_rate_container_height_entry = IntEntry(master=self.spatial_sampling_rate_container, value=self.filter["settings"]["spatial_sampling_rate"][1], justify="center", width=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["entry"]["width"])
        self.spatial_sampling_rate_container_height_entry.set_value_range((1, None))
        self.spatial_sampling_rate_container_height_entry.grid(row=1, column=1, padx=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["entry"]["padding"][0:2], pady=self._layout_settings["settings_container"]["spatial_sampling_rate_container"]["entry"]["padding"][2:4], sticky="nswe")
        self.spatial_sampling_rate_container_height_entry.set_int_var(self.spatial_sampling_rate_container_height)

        self.type_container = customtkinter.CTkFrame(master=self.settings_container, border_width=self._layout_settings["settings_container"]["type_container"]["border_width"])
        self.type_container.grid(row=3, column=0, padx=self._layout_settings["settings_container"]["type_container"]["padding"][0:2], pady=self._layout_settings["settings_container"]["type_container"]["padding"][2:4], sticky="nswe")
        self.type_container.grid_columnconfigure(0, weight=1)
        self.type_container.grid_columnconfigure(1, weight=1)

        self.type_container_name_label = customtkinter.CTkLabel(master=self.type_container, textvariable=root.current_lang.get("filter_window_settings_container_type"))
        self.type_container_name_label.grid(row=0, column=0, columnspan=2, padx=self._layout_settings["settings_container"]["type_container"]["label"]["padding"][0:2], pady=self._layout_settings["settings_container"]["type_container"]["label"]["padding"][2:4], sticky="nswe")
        self.type_container_combobox = customtkinter.CTkOptionMenu(master=self.type_container, values=[self.type_langs[key].get() for key in self.type_langs], command=self.change_type)
        self.type_container_combobox.grid(row=1, column=0, padx=self._layout_settings["settings_container"]["type_container"]["combobox"]["padding"][0:2], pady=self._layout_settings["settings_container"]["type_container"]["combobox"]["padding"][2:4], sticky="nswe")
        self.type_container_combobox.set(self.type_langs[self.filter["settings"]["type"]].get())
        self.after(100, self.resize_settings_container)

    def change_type(self, *args):
        if self.filter is not None and self.type_container_combobox is not None:
            default_type_name = self.get_type_langs_key(self.type_container_combobox.get())
            if default_type_name in root.all_filter_types:
                self.filter["settings"]["type"] = default_type_name
                self.clear_grid_container()
                self.build_grid_container()
                self.update()

    def schedule_fit(self):
        if hasattr(self, "_fit_after_id") and self._fit_after_id:
            self.after_cancel(self._fit_after_id)
        self._fit_after_id = self.after(50, self._fit_now)

    def _fit_now(self):
        self.update_idletasks()
        self.wm_geometry("")
        self._fit_after_id = None

    def update_cells(self, *args):
        if self.filter is not None:
            if self.filter["settings"]["mutable"] is True:
                self.filter["grid"] = []
                sum: float = 0.0
                for x in range(self.grid_size[0]):
                    y_list = []
                    for y in range(self.grid_size[1]):
                        cell = self.grid[x][y]
                        if cell is not None:
                            data = cell.get_cell_data()
                            sum += data["value"]
                            y_list.append(data)
                    self.filter["grid"].append(y_list)
                if self.filter["settings"]["type"] == "smoothing":
                    if sum != 0.0:
                        self.filter["settings"]["factor"] = 1 / sum
                    else:
                        self.filter["settings"]["factor"] = 0.0
                else:
                    self.filter["settings"]["factor"] = 0.0
                self.updater(self.filter)

    def update(self, *args):
        if self.filter is not None:
            if self.filter["settings"]["mutable"] is True:
                assert self.size_container_width is not None and self.size_container_height is not None and self.spatial_sampling_rate_container_width_entry is not None and self.spatial_sampling_rate_container_height_entry is not None and self.settings_container_name_str is not None
                if self.grid_size[0] != self.size_container_width.get() or self.grid_size[1] != self.size_container_height.get():
                    self.clear_grid_container()
                    self.grid_size = (self.size_container_width.get(), self.size_container_height.get())
                    self.filter["settings"]["size"] = list(self.grid_size)
                    self.build_grid_container()
                    self.update()
                    return
                self.filter["settings"]["spatial_sampling_rate"] = [self.spatial_sampling_rate_container_width_entry.get_int(), self.spatial_sampling_rate_container_height_entry.get_int()]
                self.filter["name"] = self.settings_container_name_str.get()
                self.update_cells()
        self.updater(self.filter)
        self.schedule_fit()
