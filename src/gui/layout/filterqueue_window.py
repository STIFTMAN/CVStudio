from src.gui.components.comboboxextended import ComboBoxExtended
from src.gui.components.drag_and_drop import DragAndDropLockedFrame
from src.gui.components.filter_entry_frame import FilterEntryFrame
from src.gui.layout.info_window import InfoWindow, WindowType
from src.gui.state import root
from src.gui.utils.config_loader import get_setting
import customtkinter


class FilterqueueWindow(customtkinter.CTkToplevel):

    func_bar: customtkinter.CTkFrame | None = None

    drag_and_drop_frame: DragAndDropLockedFrame | None = None

    def __init__(self, master, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.iconbitmap("src/assets/favicon.ico")
        filterqueue_window_size = get_setting("window_size")["filterqueue"]
        screen_coords = (int((master.winfo_screenwidth() - filterqueue_window_size[0]) / 2), int((master.winfo_screenheight() - filterqueue_window_size[1]) / 2))
        self.geometry(f"{filterqueue_window_size[0]}x{filterqueue_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.after(100, self.focus)
        self.minsize(filterqueue_window_size[0], filterqueue_window_size[1])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.build_func_bar()

        self.drag_and_drop_frame = DragAndDropLockedFrame(self)

        filter = root.current_project.get_filter()
        if filter is not None:
            for i in filter:
                frame = FilterEntryFrame(master=self.drag_and_drop_frame, filter=i, border_width=2, corner_radius=0)
                self.drag_and_drop_frame.add(frame)
        self.drag_and_drop_frame.grid(row=1, column=0, sticky="nswe")
        self.drag_and_drop_frame.show()

    def build_func_bar(self) -> None:
        self.func_bar = customtkinter.CTkFrame(master=self, fg_color="transparent")
        self.func_bar.grid(row=0, column=0, sticky="we")

        self.func_bar.grid_columnconfigure(3, weight=1)
        self.func_bar.grid_rowconfigure(0, weight=1)

        save_button: customtkinter.CTkButton = customtkinter.CTkButton(master=self.func_bar, textvariable=root.current_lang.get("filterqueue_window_func_bar_save_button"), command=self.save_filter)
        save_button.grid(row=0, column=0, padx=10, pady=10, sticky="nsw")

        create_new_filter_button: customtkinter.CTkButton = customtkinter.CTkButton(master=self.func_bar, textvariable=root.current_lang.get("filterqueue_window_func_bar_create_new_filter_button"))
        create_new_filter_button.grid(row=0, column=1, padx=[0, 10], pady=10, sticky="nsw")

        filter_add_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=self.func_bar, fg_color="transparent")
        filter_add_frame.grid(row=0, column=3, sticky="nse")

        filter_add_optionmenu: ComboBoxExtended = ComboBoxExtended(master=filter_add_frame, values=[key for key in root.all_filters])
        filter_add_optionmenu.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        filter_add_button: customtkinter.CTkButton = customtkinter.CTkButton(master=filter_add_frame, textvariable=root.current_lang.get("filterqueue_window_func_bar_filter_add_button"), width=28)
        filter_add_button.grid(row=0, column=1, padx=[0, 10], pady=10, sticky="nse")

    def save_filter(self):
        if not root.current_project.save():
            InfoWindow(master=self, text="Error", type=WindowType.ERROR)
        else:
            InfoWindow(master=self, text="Saved!", type=WindowType.INFO)
