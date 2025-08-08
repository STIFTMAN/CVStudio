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

    layout_settings: dict = {}

    def __init__(self, master: tkinterdnd2.Tk, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.layout_settings = get_setting("styles")["upload_window"]
        self.iconbitmap("src/assets/favicon.ico")
        upload_window_size = get_setting("window_size")["upload"]
        screen_coords = (int((master.winfo_screenwidth() - upload_window_size[0]) / 2), int((master.winfo_screenheight() - upload_window_size[1]) / 2))
        self.geometry(f"{upload_window_size[0]}x{upload_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.after(200, self.focus)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.upload_label = customtkinter.CTkLabel(master=self, textvariable=root.current_lang.get("upload_window_upload_label"), corner_radius=self.layout_settings["upload_label"]["corner_radius"], fg_color=self.layout_settings["upload_label"]["fg_color"])
        self.upload_label.grid(row=0, column=0, sticky="nsew", padx=self.layout_settings["upload_label"]["padding"][0:2], pady=self.layout_settings["upload_label"]["padding"][2:4])

        self.upload_label.drop_target_register(DND_FILES)  # type: ignore
        self.upload_label.dnd_bind('<<Drop>>', self.on_drop)  # type: ignore

        self.upload_filedialog_button = customtkinter.CTkButton(master=self, textvariable=root.current_lang.get("upload_window_upload_filedialog_button"), command=self.filediloag_submit)
        self.upload_filedialog_button.grid(row=1, column=0, sticky="ew", padx=self.layout_settings["upload_filedialog_button"]["padding"][0:2], pady=self.layout_settings["upload_filedialog_button"]["padding"][2:4])

    def filediloag_submit(self):
        filepath = filedialog.askopenfilename(title=root.current_lang.get("upload_window_filedialog_window_title").get(), filetypes=[(root.current_lang.get("upload_window_filedialog_select_type_pretext").get(), "*.jpg;*.jpeg;*.png;*.bmp;*.gif")])
        if os.path.isfile(filepath) and filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            root.current_project.load_image(cv2.imread(filepath))
            self.master.event_generate("<<UploadClosed>>")
            self.destroy()

    def on_drop(self, event):
        filepath = event.data.strip("{}")
        if os.path.isfile(filepath) and filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            root.current_project.load_image(cv2.imread(filepath))
            self.master.event_generate("<<UploadClosed>>")
            self.destroy()
