from src.gui.utils.config_loader import get_setting
import customtkinter

window: customtkinter.CTkToplevel | None = None


def build(app: customtkinter.CTk):
    global window
    if window is not None and window.winfo_exists():
        window.focus()
        return
    window = customtkinter.CTkToplevel(master=app)

    filterqueue_window_size = get_setting("window_size")["filterqueue"]
    screen_coords = (int((app.winfo_screenwidth() - filterqueue_window_size[0]) / 2), int((app.winfo_screenheight() - filterqueue_window_size[1]) / 2))

    window.geometry(f"{filterqueue_window_size[0]}x{filterqueue_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
    window.after(100, window.focus)
