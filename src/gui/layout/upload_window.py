import tkinterdnd2
import src.gui.state.root as root
from src.gui.utils.config_loader import get_setting
import customtkinter
from tkinterdnd2 import DND_FILES
import os
import cv2
from tkinter import filedialog


class UploadWindow(customtkinter.CTkToplevel):

    upload_label: customtkinter.CTkLabel | None = None

    upload_filedialog_button: customtkinter.CTkButton | None = None

    text: customtkinter.CTkLabel | None = None

    def __init__(self, master: tkinterdnd2.Tk, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.iconbitmap("src/assets/favicon.ico")
        upload_window_size = get_setting("window_size")["upload"]
        screen_coords = (int((master.winfo_screenwidth() - upload_window_size[0]) / 2), int((master.winfo_screenheight() - upload_window_size[1]) / 2))
        self.geometry(f"{upload_window_size[0]}x{upload_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.after(200, self.focus)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.resizable(False, False)
        self.upload_label = customtkinter.CTkLabel(master=self, text="Upload", corner_radius=10, fg_color="green")
        self.upload_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.upload_label.drop_target_register(DND_FILES)  # type: ignore
        self.upload_label.dnd_bind('<<Drop>>', self.on_drop)  # type: ignore

        self.upload_filedialog_button = customtkinter.CTkButton(master=self, text="Search File")
        self.upload_filedialog_button.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 30))

    def on_drop(self, event):
        filepath = event.data.strip("{}")
        if os.path.isfile(filepath) and filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            root.current_project.load_image(cv2.imread(filepath))
            self.destroy()
        else:
            print("Kein Unterstütztes Format!")
