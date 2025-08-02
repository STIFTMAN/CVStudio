import tkinterdnd2
import src.gui.state.root as root
from src.gui.utils.config_loader import get_setting
import customtkinter
from tkinterdnd2 import DND_FILES
import os
import cv2
from src.gui.utils.cv2_toctkimage import cv2_to_ctkimage
import json


class UploadWindow(customtkinter.CTkToplevel):

    upload_label: customtkinter.CTkLabel | None = None

    text: customtkinter.CTkLabel | None = None

    def __init__(self, master: tkinterdnd2.Tk, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.iconbitmap("src/assets/favicon.ico")
        upload_window_size = get_setting("window_size")["upload"]
        screen_coords = (int((master.winfo_screenwidth() - upload_window_size[0]) / 2), int((master.winfo_screenheight() - upload_window_size[1]) / 2))
        self.geometry(f"{upload_window_size[0]}x{upload_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.after(100, self.focus)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.upload_label = customtkinter.CTkLabel(master=self, text="Upload", fg_color="red")
        self.upload_label.grid(row=0, column=0, sticky="nsew")

        self.upload_label.drop_target_register(DND_FILES)  # type: ignore
        self.upload_label.dnd_bind('<<Drop>>', self.on_drop)  # type: ignore

    def on_drag(self):
        print("dragging")

    def on_drop(self, event):
        filepath = event.data.strip("{}")
        if os.path.isfile(filepath) and filepath.lower().endswith(('.json')):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                root.project.get_json(data)
                print(root.project.json)
        elif os.path.isfile(filepath) and filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            img: customtkinter.CTkImage = cv2_to_ctkimage(cv2.imread(filepath))
            assert self.upload_label is not None
            self.upload_label.configure(image=img, text="")
        else:
            print("Kein Unterstütztes Format!")
