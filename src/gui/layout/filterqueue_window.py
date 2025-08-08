from src.gui.components.drag_and_drop import DragAndDropLockedFrame
from src.gui.utils.config_loader import get_setting
import customtkinter


class FilterqueueWindow(customtkinter.CTkToplevel):

    drag_and_drop_frame: DragAndDropLockedFrame | None = None

    def __init__(self, master, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.iconbitmap("src/assets/favicon.ico")
        filterqueue_window_size = get_setting("window_size")["filterqueue"]
        screen_coords = (int((master.winfo_screenwidth() - filterqueue_window_size[0]) / 2), int((master.winfo_screenheight() - filterqueue_window_size[1]) / 2))
        self.geometry(f"{filterqueue_window_size[0]}x{filterqueue_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.after(100, self.focus)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.drag_and_drop_frame = DragAndDropLockedFrame(self)

        for i in range(10):
            frame = customtkinter.CTkFrame(master=self.drag_and_drop_frame, border_width=10, corner_radius=0)
            label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=frame, text=str(i), corner_radius=0)
            label.pack(padx=10, pady=20)
            self.drag_and_drop_frame.add(frame)
        self.drag_and_drop_frame.grid(sticky="nswe")
        self.drag_and_drop_frame.show()
