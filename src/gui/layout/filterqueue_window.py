from src.gui.utils.config_loader import get_setting
import customtkinter


class FilterqueueWindow(customtkinter.CTkToplevel):

    def __init__(self, master: customtkinter.CTk, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.iconbitmap("src/assets/favicon.ico")
        filterqueue_window_size = get_setting("window_size")["filterqueue"]
        screen_coords = (int((master.winfo_screenwidth() - filterqueue_window_size[0]) / 2), int((master.winfo_screenheight() - filterqueue_window_size[1]) / 2))
        self.geometry(f"{filterqueue_window_size[0]}x{filterqueue_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.after(100, self.focus)

