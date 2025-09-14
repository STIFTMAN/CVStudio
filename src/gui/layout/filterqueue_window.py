import copy
from src.gui.components.comboboxextended import ComboBoxExtended
from src.gui.components.drag_and_drop import DragAndDropLockedFrame
from src.gui.components.filter_entry_frame import FilterEntryFrame
from src.gui.layout.info_window import InfoWindow, WindowType
from src.gui.state import root
from src.gui.state.project_file_type import Filter_Type, empty_filter
from src.gui.utils.config_loader import get_setting
import customtkinter
import uuid


class FilterqueueWindow(customtkinter.CTkToplevel):

    func_bar: customtkinter.CTkFrame | None = None

    drag_and_drop_frame: DragAndDropLockedFrame | None = None

    comboboxextended: ComboBoxExtended | None = None

    _layout_settings: dict = {}

    def __init__(self, master, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.after(250, lambda: self.iconbitmap("src/assets/favicon.ico"))
        filterqueue_window_size = get_setting("window_size")["filterqueue"]
        screen_coords = (int((master.winfo_screenwidth() - filterqueue_window_size[0]) / 2), int((master.winfo_screenheight() - filterqueue_window_size[1]) / 2))
        self.geometry(f"{filterqueue_window_size[0]}x{filterqueue_window_size[1]}+{screen_coords[0] + 10 }+{screen_coords[1] + 10}")
        self.after(100, self.focus)
        self._layout_settings = get_setting("styles")["filterqueue_window"]
        self.minsize(filterqueue_window_size[0], filterqueue_window_size[1])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.build_func_bar()

        self.drag_and_drop_frame = DragAndDropLockedFrame(self)
        self.drag_and_drop_frame.set_border_width(get_setting("components")["filter_entry_frame"]["padding"])
        self.drag_and_drop_frame.grid(row=1, column=0, sticky="nswe")
        self.drag_and_drop_frame.show()
        self.drag_and_drop_frame.set_updater(self.save_new_order)
        self.build_filter_list()

    def save_new_order(self):
        root.current_project.data["filterqueue"] = [i.id for i in self.drag_and_drop_frame.get_frames()]  # type: ignore
        self.save_project()
        self.update_combobox()

    def build_filter_list(self):
        if self.drag_and_drop_frame is not None:
            self.drag_and_drop_frame.clear()
            queue_ids = root.current_project.get_queue()
            for i in range(len(queue_ids)):
                action = root.current_project.get_action_by_id(queue_ids[i])
                if action is not None:
                    frame = FilterEntryFrame(master=self.drag_and_drop_frame, action=action, id=queue_ids[i])
                    frame.set_updater(updater=self.update_filter)
                    frame.set_deleter(deleter=self.delete_action)
                    self.drag_and_drop_frame.add(frame)
            self.drag_and_drop_frame.show()

    def update_filter(self, frame: FilterEntryFrame, data: Filter_Type):
        if frame.id is not None:
            self.save_filter(frame.id, data)
            ids = root.current_project.count_ids(frame.id)
            if len(ids) > 1 and self.drag_and_drop_frame is not None:
                assert frame.id is not None
                frames = self.drag_and_drop_frame.get_frames()
                for i in range(len(frames)):
                    if frames[i] == frame:
                        continue
                    if i in ids:
                        f = frames[i]
                        assert isinstance(f, FilterEntryFrame)
                        f.get_update(data)

    def create_new_filter(self):
        id = str(uuid.uuid4())
        new_filter = copy.deepcopy(empty_filter)
        new_filter["name"] = "NewFilter-" + id[0:8]
        root.all_filters[id] = {"type": "filter", "data": new_filter}
        root.current_project.add_filter(id)
        from src.gui.utils.project_loader import save_filter
        save_filter()
        self.save_project()
        self.update_combobox()
        self.build_filter_list()

    def delete_action(self, frame: FilterEntryFrame):
        if self.drag_and_drop_frame is not None:
            key = -1
            assert frame.id is not None
            id = frame.id
            frames = self.drag_and_drop_frame.get_frames()
            for i in range(len(frames)):
                if frames[i] == frame:
                    key = i
                    break
            self.drag_and_drop_frame.delete_item_by_index(key)
            self.drag_and_drop_frame.show()
            root.current_project.delete_filter(id, key)

    def destroy(self):
        super().destroy()

    def build_func_bar(self) -> None:
        self.func_bar = customtkinter.CTkFrame(master=self, fg_color="transparent")
        self.func_bar.grid(row=0, column=0, sticky="we")

        [self.func_bar.grid_columnconfigure(i, weight=1) for i in range(3)]
        self.func_bar.grid_rowconfigure(0, weight=1)

        create_new_filter_button: customtkinter.CTkButton = customtkinter.CTkButton(master=self.func_bar, textvariable=root.current_lang.get("filterqueue_window_func_bar_create_new_filter_button"), command=self.create_new_filter)
        create_new_filter_button.grid(row=0, column=0, padx=self._layout_settings["func_bar"]["create_new_filter_button"]["padding"][0:2], pady=self._layout_settings["func_bar"]["create_new_filter_button"]["padding"][2:4], sticky="nsw")

        self.comboboxextended = ComboBoxExtended(master=self.func_bar, values=[])
        self.comboboxextended.grid(row=0, column=2, padx=self._layout_settings["func_bar"]["comboboxextended"]["padding"][0:2], pady=self._layout_settings["func_bar"]["comboboxextended"]["padding"][2:4], sticky="ns")
        self.comboboxextended.set_updater(self.get_comobox_value)

        self.update_combobox()

    def get_comobox_value(self, data: tuple[str, str]):
        root.current_project.add_filter(data[1])
        self.save_project()
        self.build_filter_list()

    def update_combobox(self):
        values: list[tuple[str, str]] = []
        for key in root.all_filters:
            f = root.all_filters[key]["data"]
            if type(f) is str:
                values.append((f, key))
            else:
                values.append((f["name"], key))  # type: ignore
        if self.comboboxextended is not None:
            self.comboboxextended.set_values(values)

    def save_project(self):
        if not root.current_project.save():
            InfoWindow(master=self, text="Error!", type=WindowType.ERROR)

    def save_filter(self, id: str, f: Filter_Type):
        root.current_project.save_filter(id, f)
        self.update_combobox()
