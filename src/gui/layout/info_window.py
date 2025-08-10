from enum import IntEnum
from src.gui.utils.config_loader import get_setting
import customtkinter


class WindowType(IntEnum):
    INFO = 1
    ERROR = 2


class InfoWindow(customtkinter.CTkToplevel):

    text_label: customtkinter.CTkLabel | None = None

    def __init__(self, master, text: str = "", type: WindowType = WindowType.INFO, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.iconbitmap("src/assets/favicon.ico")
        info_window_size = get_setting("window_size")["info"]
        screen_coords = (int((master.winfo_screenwidth() - info_window_size[0]) / 2), int((master.winfo_screenheight() - info_window_size[1]) / 2))
        self.geometry(f"{info_window_size[0]}x{info_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.after(100, self.focus)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.label = customtkinter.CTkLabel(master=self, text=text)
        self.label.grid(sticky="nswe", row=0, column=0)
        if type == WindowType.INFO:
            self.after(2000, self.destroy)
