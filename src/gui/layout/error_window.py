from src.gui.utils.config_loader import get_setting
import customtkinter


class ErrorWindow(customtkinter.CTkToplevel):

    text_label: customtkinter.CTkLabel | None = None

    def __init__(self, master, text: str = "", *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.iconbitmap("src/assets/favicon.ico")
        error_window_size = get_setting("window_size")["error"]
        screen_coords = (int((master.winfo_screenwidth() - error_window_size[0]) / 2), int((master.winfo_screenheight() - error_window_size[1]) / 2))
        self.geometry(f"{error_window_size[0]}x{error_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.after(100, self.focus)
        self.label = customtkinter.CTkLabel(master=self, text=text)
        self.label.grid(sticky="nswe", row=0, column=0)
