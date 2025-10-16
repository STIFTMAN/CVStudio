from typing import Callable
import customtkinter
from src.gui.layout.upload_window import UploadWindow
from src.gui.state.error import Error
from src.gui.utils.project import Project
from src.gui.utils.resize_image import resize_image_to_label
from src.gui.layout.filterqueue_window import FilterqueueWindow
from src.gui.layout.test_window import TestWindow
from src.gui.utils.config_loader import get_setting, save_settings
import src.gui.state.root as root
from src.gui.components.dropdownmenu import Dropdownmenu
from src.gui.components.tabviewextended import TabviewExtended
import webbrowser
import re
from tkinterdnd2 import TkinterDnD
import threading
import cv2
import numpy
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED
from typing import Optional
import src.gui.utils.logger as log


class MainWindow(TkinterDnD.Tk):
    nav_frame: Dropdownmenu | None = None
    container_frame: customtkinter.CTkFrame | customtkinter.CTkScrollableFrame | None = None
    filterqueue_window: FilterqueueWindow | None = None
    test_window: TestWindow | None = None
    progress: customtkinter.DoubleVar | None = None
    upload_window: UploadWindow | None = None
    layout_settings: dict = {}
    image_labels: list[customtkinter.CTkLabel | None] = [None, None]
    status_label: customtkinter.CTkLabel | None = None
    progressbar: customtkinter.CTkProgressBar | None = None

    progress_test: customtkinter.DoubleVar | None = None
    reload_button: customtkinter.CTkButton | None = None

    def __init__(self):
        super().__init__()

    def build(self):
        self.change_title()
        self.iconbitmap("src/assets/favicon.ico")
        window_size = get_setting("window_size")["main"]
        screen_coords = (int((self.winfo_screenwidth() - window_size[0]) / 2), int((self.winfo_screenheight() - window_size[1]) / 2))
        self.geometry(f"{window_size[0]}x{window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.minsize(window_size[0], window_size[1])
        self.layout_settings = get_setting("styles")["main_window"]
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.build_nav_frame()
        self.build_init_container_frame()
        if root.all_keybindings is not None:
            for key in root.all_keybindings:
                self.bind_all(root.all_keybindings[key], lambda event, k=key: self.event(k))
        self.progress = customtkinter.DoubleVar(value=0.0)
        self.progress.trace_add("write", self.observe_progress)
        root.current_project.set_progress(self.progress)
        self.progress_test = customtkinter.DoubleVar(value=0.0)
        root.current_project.set_progress_test(self.progress_test)
        root.status = customtkinter.StringVar(value=root.current_lang.get("project_apply_action_queue_status_init").get())
        root.status_details = customtkinter.StringVar(value="")
        root.status_test = customtkinter.StringVar(value="")

    def change_title(self):
        if root.current_project.data is not None:
            self.title(f"{get_setting('name')} | [{root.current_project.name}]")
        else:
            self.title(get_setting("name"))

    def observe_progress(self, *args):
        if self.progress:
            val = self.progress.get()
            if val >= 1.0:
                self.resize_images(None)

    def build_nav_frame(self):
        self.nav_frame = Dropdownmenu(master=self)
        self.nav_frame.addButton("main_window_dropdownmenu_home", root.current_lang.get("main_window_dropdownmenu_home"), self.build_home)
        self.nav_frame.add("main_window_dropdownmenu_project", root.current_lang.get("main_window_dropdownmenu_project"), root.current_lang.get("main_window_dropdownmenu_project_save_image_result"), lambda: self.save_images_via_dialog(True))
        self.nav_frame.add("main_window_dropdownmenu_project", root.current_lang.get("main_window_dropdownmenu_project"), root.current_lang.get("main_window_dropdownmenu_project_save_image_result_all"), self.save_images_via_dialog)
        self.nav_frame.add("main_window_dropdownmenu_project", root.current_lang.get("main_window_dropdownmenu_project"), root.current_lang.get("main_window_dropdownmenu_project_close"), self.reset_project)
        self.nav_frame.add("main_window_dropdownmenu_project", root.current_lang.get("main_window_dropdownmenu_project"), root.current_lang.get("main_window_dropdownmenu_project_open_filterqueue"), self.open_filterqueue_window)
        self.nav_frame.add("main_window_dropdownmenu_project", root.current_lang.get("main_window_dropdownmenu_project"), root.current_lang.get("main_window_dropdownmenu_project_open_upload_image"), self.open_upload_window)
        self.nav_frame.addButton("main_window_dropdownmenu_testing", root.current_lang.get("main_window_dropdownmenu_testing"), self.open_test_window)
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_look"), lambda: self.build_settings("main_window_settings_look"))
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_keybindings"), lambda: self.build_settings("main_window_settings_keybindings"))
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_about"), lambda: self.build_settings("main_window_settings_about"))
        self.nav_frame.grid(row=0, column=0, sticky="we")
        self.nav_frame.outside_tracking(self)

    def reset_project(self):
        root.current_project.reset()
        self.reset_container_frame()
        self.change_title()
        self.build_init_container_frame()
        if self.filterqueue_window is not None:
            self.filterqueue_window.destroy()
            self.filterqueue_window = None
        if self.upload_window is not None:
            self.upload_window.destroy()
            self.upload_window = None

    def build_home(self):
        self.reset_container_frame()
        if root.current_project.ready():
            self.build_image_container()
        else:
            self.build_init_container_frame()

    def build_init_container_frame(self):
        if self.container_frame is None:
            self.container_frame = customtkinter.CTkFrame(master=self, corner_radius=0)
            self.container_frame.grid(row=1, column=0, sticky="nswe")
        self.container_frame.grid_columnconfigure(0, weight=1)
        self.container_frame.grid_columnconfigure(1, weight=1)
        self.container_frame.grid_rowconfigure(0, weight=1)
        open_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=self.container_frame)
        open_frame.grid(row=0, column=0, sticky="nswe", padx=self.layout_settings["init"]["open"]["padding"][0:2], pady=self.layout_settings["init"]["open"]["padding"][2:4])

        open_frame.grid_columnconfigure(0, weight=1)
        open_frame.grid_rowconfigure(0, weight=1)
        if len(root.all_projects) > 0:
            open_frame.grid_rowconfigure(4, weight=2)

            open_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=open_frame, font=(self.layout_settings["init"]["open"]["label"]["font"], self.layout_settings["init"]["open"]["label"]["font_size"]), textvariable=root.current_lang.get("main_window_init_open_label"))
            open_label.grid(row=1, column=0, sticky="we", padx=self.layout_settings["init"]["open"]["label"]["padding"][0:2], pady=self.layout_settings["init"]["open"]["label"]["padding"][2:4])

            open_optionmenu: customtkinter.CTkOptionMenu = customtkinter.CTkOptionMenu(master=open_frame, values=[key for key in root.all_projects], anchor="center")
            open_optionmenu.grid(row=2, column=0, sticky="we", padx=self.layout_settings["init"]["open"]["optionmenu"]["padding"][0:2], pady=self.layout_settings["init"]["open"]["optionmenu"]["padding"][2:4])

            open_button: customtkinter.CTkButton = customtkinter.CTkButton(master=open_frame, textvariable=root.current_lang.get("main_window_init_open_label"), command=lambda: self.init_open_button_submit(open_optionmenu))
            open_button.grid(row=3, column=0, sticky="we", padx=self.layout_settings["init"]["open"]["button"]["padding"][0:2], pady=self.layout_settings["init"]["open"]["button"]["padding"][2:4])
        else:
            open_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=open_frame, font=(self.layout_settings["init"]["open"]["label"]["font"], self.layout_settings["init"]["open"]["label"]["font_size"]), textvariable=root.current_lang.get("main_window_init_open_label_no_project"))
            open_label.grid(row=0, column=0, sticky="nswe")

        create_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=self.container_frame)
        create_frame.grid(row=0, column=1, sticky="nswe", padx=self.layout_settings["init"]["create"]["padding"][0:2], pady=self.layout_settings["init"]["create"]["padding"][2:4])

        create_frame.grid_columnconfigure(0, weight=1)
        create_frame.grid_rowconfigure(0, weight=1)
        create_frame.grid_rowconfigure(4, weight=2)

        create_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=create_frame, font=(self.layout_settings["init"]["create"]["label"]["font"], self.layout_settings["init"]["create"]["label"]["font_size"]), textvariable=root.current_lang.get("main_window_init_create_label"))
        create_label.grid(row=1, column=0, sticky="we", padx=self.layout_settings["init"]["create"]["label"]["padding"][0:2], pady=self.layout_settings["init"]["create"]["label"]["padding"][2:4])

        create_entry: customtkinter.CTkEntry = customtkinter.CTkEntry(master=create_frame, justify="center", placeholder_text=root.current_lang.get("main_window_init_create_entry_placeholder").get())
        create_entry.grid(row=2, column=0, sticky="we", padx=self.layout_settings["init"]["create"]["entry"]["padding"][0:2], pady=self.layout_settings["init"]["create"]["entry"]["padding"][2:4])

        create_button: customtkinter.CTkButton = customtkinter.CTkButton(master=create_frame, state="disabled", textvariable=root.current_lang.get("main_window_init_create_button"))
        create_button.grid(row=3, column=0, sticky="we", padx=self.layout_settings["init"]["create"]["button"]["padding"][0:2], pady=self.layout_settings["init"]["create"]["button"]["padding"][2:4])

        create_button.configure(command=lambda: self.init_create_button_submit(create_entry))
        create_entry.bind("<KeyRelease>", lambda e: self.init_create_entry_validate(create_entry, create_button))

    def init_create_entry_validate(self, entry: customtkinter.CTkEntry, button: customtkinter.CTkButton):
        if Project.valid_filename(str(entry.get())):
            entry.configure(border_color="green")
            button.configure(state="normal")
        else:
            entry.configure(border_color="red")
            button.configure(state="disabled")

    def init_create_button_submit(self, entry: customtkinter.CTkEntry):
        if Project.create(entry.get()):
            self.build_image_container()
        else:
            log.log.write(text=Error.CREATE_PROJECT.value, tag="ERROR", modulename=Path(__file__).stem)

    def init_open_button_submit(self, optionmenu: customtkinter.CTkOptionMenu):
        data = optionmenu.get()
        root.current_project.load_data(data, root.all_projects[data])
        self.change_title()
        self.build_image_container()

    def build_image_container(self):
        self.reset_container_frame()

        select_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=self.container_frame)
        select_frame.grid(row=0, column=0, padx=self.layout_settings["image_container"]["padding"][0:2], pady=self.layout_settings["image_container"]["padding"][2:4], sticky="nwe")
        select_frame.grid_columnconfigure(0, weight=1)
        select_frame.grid_columnconfigure(1, minsize=300)
        assert self.container_frame is not None
        self.container_frame.grid_rowconfigure(0, weight=0)
        self.container_frame.grid_rowconfigure(1, weight=1)

        status_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=select_frame)
        status_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)
        status_frame.grid_rowconfigure(0, weight=1)

        self.status_label = customtkinter.CTkLabel(master=status_frame, textvariable=root.status)
        self.status_label.grid(row=0, column=0, padx=self.layout_settings["image_container"]["select_frame"]["status_label"]["padding"][0:2], pady=self.layout_settings["image_container"]["select_frame"]["status_label"]["padding"][2:4])

        self.status_details_label = customtkinter.CTkLabel(master=status_frame, textvariable=root.status_details)
        self.status_details_label.grid(row=0, column=1, padx=self.layout_settings["image_container"]["select_frame"]["status_label"]["padding"][0:2], pady=self.layout_settings["image_container"]["select_frame"]["status_label"]["padding"][2:4])

        progressbar_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=select_frame)
        progressbar_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        progressbar_frame.grid_columnconfigure(0, weight=1)
        progressbar_frame.grid_rowconfigure(0, weight=1)

        self.progressbar = customtkinter.CTkProgressBar(master=progressbar_frame, variable=self.progress)
        self.progressbar.grid(row=0, column=0, sticky="we", padx=self.layout_settings["image_container"]["select_frame"]["progressbar"]["padding"][0:2], pady=self.layout_settings["image_container"]["select_frame"]["progressbar"]["padding"][2:4])

        switch_mode: customtkinter.CTkSwitch = customtkinter.CTkSwitch(master=select_frame, textvariable=root.current_lang.get("main_window_image_container_select_compare"))
        switch_mode.grid(row=0, column=2, padx=self.layout_settings["image_container"]["select_frame"]["switch_mode"]["padding"][0:2], pady=self.layout_settings["image_container"]["select_frame"]["switch_mode"]["padding"][2:4])

        self.reload_button = customtkinter.CTkButton(master=select_frame, textvariable=root.current_lang.get("main_window_image_container_select_reload"))
        self.reload_button.grid(row=0, column=3, padx=self.layout_settings["image_container"]["select_frame"]["reload_button"]["padding"][0:2], pady=self.layout_settings["image_container"]["select_frame"]["reload_button"]["padding"][2:4])

        assert root.current_project.data is not None
        switch_mode.select(root.current_project.data["image_view_mode"])

        image_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=self.container_frame)
        image_frame.grid(row=1, column=0, padx=self.layout_settings["image_container"]["image_frame"]["padding"][0:2], pady=self.layout_settings["image_container"]["image_frame"]["padding"][2:4], sticky="nswe")

        switch_mode.configure(command=lambda: self.build_image_container_image_frame(image_frame, bool(switch_mode.get())))

        self.build_image_container_image_frame(image_frame, root.current_project.data["image_view_mode"])
        self.reload_button.configure(command=self.start_action_queue_thread)

        self.open_filterqueue_window()

    def build_image_container_image_frame(self, image_frame: customtkinter.CTkFrame, mode: bool):
        for widget in image_frame.winfo_children():
            widget.destroy()
        image_frame.columnconfigure(0, weight=1)
        self.image_labels = [None, None]
        image_frame.rowconfigure(0, weight=1)
        self.image_labels[1] = customtkinter.CTkLabel(master=image_frame, text="")
        if mode:
            self.image_labels[1].grid(row=0, column=1, padx=self.layout_settings["image_container"]["image_frame"]["image_label_2"]["padding"][0:2], pady=self.layout_settings["image_container"]["image_frame"]["image_label_2"]["padding"][2:4], sticky="nswe")
            self.image_labels[0] = customtkinter.CTkLabel(master=image_frame, text="")
            self.image_labels[0].grid(row=0, column=0, padx=self.layout_settings["image_container"]["image_frame"]["image_label_1"]["padding"][0:2], pady=self.layout_settings["image_container"]["image_frame"]["image_label_1"]["padding"][2:4], sticky="nswe")
            image_frame.columnconfigure(1, weight=1)
        else:
            self.image_labels[1].grid(row=0, column=0, padx=self.layout_settings["image_container"]["image_frame"]["image_label_2"]["padding"][0:2], pady=self.layout_settings["image_container"]["image_frame"]["image_label_2"]["padding"][2:4], sticky="nswe")
            image_frame.columnconfigure(1, weight=0)
        if root.current_project.image_ready():
            assert root.current_project.image is not None
            if self.image_labels[0] is not None:
                self.image_labels[0].bind("<Configure>", self.resize_images)
            if self.image_labels[1] is not None:
                self.image_labels[1].bind("<Configure>", self.resize_images)
            self.resize_images(None)

    def reset_container_frame(self):
        if self.container_frame is not None:
            for widget in self.container_frame.winfo_children():
                widget.destroy()
            [self.container_frame.grid_columnconfigure(i, weight=0) for i in range(20)]
            [self.container_frame.grid_rowconfigure(i, weight=0) for i in range(20)]

    def build_settings(self, tabindex: str):
        assert root.all_keybindings is not None
        self.reset_container_frame()
        headline_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=self.container_frame, textvariable=root.current_lang.get("main_window_dropdownmenu_settings"), font=("Roboto", self.layout_settings["settings"]["label"]["font_size"]))
        headline_label.pack(fill="x", side="top", padx=self.layout_settings["settings"]["label"]["padding"], pady=(self.layout_settings["settings"]["label"]["padding"], 0))

        tabview: TabviewExtended = TabviewExtended(master=self.container_frame)
        tabview.pack(fill="both", side="top", expand=True, padx=self.layout_settings["settings"]["tabview"]["padding"], pady=self.layout_settings["settings"]["tabview"]["padding"])

        tabview.add_tab("main_window_settings_look", root.current_lang.get("main_window_settings_look"))
        tabview.add_tab("main_window_settings_keybindings", root.current_lang.get("main_window_settings_keybindings"))
        tabview.add_tab("main_window_settings_about", root.current_lang.get("main_window_settings_about"))
        tabview.set(tabindex)
        tabview.tab("main_window_settings_look").grid_columnconfigure(0, weight=1)
        tabview.tab("main_window_settings_keybindings").grid_columnconfigure(0, weight=1)
        tabview.tab("main_window_settings_about").grid_columnconfigure(0, weight=1)

        settings_look_keys: list[tuple[customtkinter.StringVar, Callable, list, str]] = [
            (root.current_lang.get("main_window_settings_look_lang_label"), self.settings_look_lang_output, [root.all_lang[key] for key in root.all_lang], root.all_lang[get_setting("lang")]),
            (root.current_lang.get("main_window_settings_look_darkmode_label"), self.settings_look_darkmode_output, ["system", "dark", "light"], get_setting("darkmode")),
            (root.current_lang.get("main_window_settings_look_theme_label"), self.settings_look_theme_output, [key for key in root.all_styles], get_setting("color_theme"))
        ]

        for key in range(len(settings_look_keys)):
            settings_look_temp_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=tabview.tab("main_window_settings_look"))
            settings_look_temp_frame.grid(row=key, column=0, padx=self.layout_settings["settings"]["look"]["frame"]["padding"], pady=self.layout_settings["settings"]["look"]["frame"]["padding"], sticky="nsew")
            [settings_look_temp_frame.grid_columnconfigure(i, weight=1) for i in range(3)]

            settings_look_temp_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_look_temp_frame, anchor="w", width=self.layout_settings["settings"]["look"]["label"]["width"], textvariable=settings_look_keys[key][0])
            settings_look_temp_label.grid(row=0, column=1, padx=self.layout_settings["settings"]["look"]["label"]["padding"], pady=self.layout_settings["settings"]["look"]["label"]["padding"])

            settings_look_lang_optionmenu: customtkinter.CTkOptionMenu = customtkinter.CTkOptionMenu(master=settings_look_temp_frame, width=self.layout_settings["settings"]["look"]["optionmenu"]["width"], anchor="center", values=settings_look_keys[key][2], command=settings_look_keys[key][1])
            settings_look_lang_optionmenu.grid(row=0, column=3, padx=self.layout_settings["settings"]["look"]["optionmenu"]["padding"], pady=self.layout_settings["settings"]["look"]["optionmenu"]["padding"])
            settings_look_lang_optionmenu.set(settings_look_keys[key][3])

        settings_keybindings_keys: list[tuple[str, str]] = [
            ("main_window_settings_keybindings_quick_test_label", "quick_test"),
            ("main_window_settings_keybindings_help_label", "help"),
            ("main_window_settings_keybindings_license_label", "license"),
            ("main_window_settings_keybindings_reload_images_label", "reload_images"),
            ("main_window_settings_keybindings_save_pictures_label", "save_pictures")
        ]
        for key in range(len(settings_keybindings_keys)):

            settings_keybindings_temp_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=tabview.tab("main_window_settings_keybindings"))
            settings_keybindings_temp_frame.grid(row=key, column=0, padx=self.layout_settings["settings"]["keybindings"]["frame"]["padding"], pady=self.layout_settings["settings"]["keybindings"]["frame"]["padding"], sticky="nsew")
            [settings_keybindings_temp_frame.grid_columnconfigure(i, weight=1) for i in range(3)]

            settings_keybindings_temp_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_temp_frame, width=self.layout_settings["settings"]["keybindings"]["label"]["width"], anchor="w", textvariable=root.current_lang.get(settings_keybindings_keys[key][0]))
            settings_keybindings_temp_label.grid(row=0, column=1, padx=self.layout_settings["settings"]["keybindings"]["label"]["padding"], pady=self.layout_settings["settings"]["keybindings"]["label"]["padding"])

            settings_keybindings_temp_binding_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_temp_frame, width=self.layout_settings["settings"]["keybindings"]["binding_label"]["width"], fg_color=("grey", "black"), text_color=("white", "white"), corner_radius=5, text=re.sub(r"[<>]", "", root.all_keybindings[settings_keybindings_keys[key][1]]).replace("Control", "Ctrl").replace("-", " + "))
            settings_keybindings_temp_binding_label.grid(row=0, column=3, padx=self.layout_settings["settings"]["keybindings"]["binding_label"]["padding"], pady=self.layout_settings["settings"]["keybindings"]["binding_label"]["padding"])

        settings_about_keys: list[customtkinter.StringVar | str] = [
            get_setting("name"),
            root.version,
            root.current_lang.get("main_window_settings_about_label_description"),
            root.current_lang.get("main_window_settings_about_label_developer"),
            root.current_lang.get("main_window_settings_about_label_license"),
            get_setting("license_url")
        ]

        for key in range(len(settings_about_keys)):
            if isinstance(settings_about_keys[key], customtkinter.StringVar):
                settings_about_temp_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=tabview.tab("main_window_settings_about"), padx=self.layout_settings["settings"]["about"]["label"]["padding_inline"][0], pady=self.layout_settings["settings"]["about"]["label"]["padding_inline"][1], anchor="w", wraplength=self.layout_settings["settings"]["about"]["label"]["wraplength"], justify="left", textvariable=settings_about_keys[key])
            else:
                settings_about_temp_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=tabview.tab("main_window_settings_about"), wraplength=self.layout_settings["settings"]["about"]["label"]["wraplength"], justify="left", padx=self.layout_settings["settings"]["about"]["label"]["padding_inline"][0], pady=self.layout_settings["settings"]["about"]["label"]["padding_inline"][1], anchor="w", text=settings_about_keys[key])  # type: ignore
            settings_about_temp_label.grid(row=key, column=0, padx=self.layout_settings["settings"]["about"]["label"]["padding"][0], pady=self.layout_settings["settings"]["about"]["label"]["padding"][1], sticky="w")

    def settings_look_lang_output(self, choice):
        from src.gui.utils.lang_loader import change_lang, get_translation_from_all_lang
        translations = get_translation_from_all_lang("language_package_name")
        for key in translations:
            if translations[key] == choice:
                if root.settings is not None:
                    root.settings["lang"] = key
                    save_settings()
                    change_lang(key)
                return

    def settings_look_darkmode_output(self, choice):
        if root.settings is not None:
            root.settings["darkmode"] = choice
            save_settings()
            customtkinter.set_appearance_mode(choice)

    def settings_look_theme_output(self, choice: str):
        if root.settings is not None:
            root.settings["color_theme"] = choice
            save_settings()
            from src.gui.utils.restart import restart
            if self.filterqueue_window is not None and self.filterqueue_window.winfo_exists():
                self.filterqueue_window.destroy()
                self.filterqueue_window = None
            if self.upload_window is not None and self.upload_window.winfo_exists():
                self.upload_window.destroy()
                self.upload_window = None
            restart()

    def close_upload_window(self, event):
        if self.upload_window is not None and self.upload_window.winfo_exists():
            self.upload_window.destroy()
            self.upload_window = None
            if root.current_project.image is not None:
                root.current_project.reset_action_queue()
                if self.image_labels[0] is not None:
                    self.image_labels[0].bind("<Configure>", self.resize_images)
                if self.image_labels[1] is not None:
                    self.image_labels[1].bind("<Configure>", self.resize_images)
                self.start_action_queue_thread()

    def start_action_queue_thread(self):
        def task():
            root.current_project.apply_action_queue()
            assert root.status_details is not None
            root.status_details.set("")
        threading.Thread(target=task, daemon=True).start()

    def open_upload_window(self):
        if root.current_project.ready():
            if self.upload_window is not None and self.upload_window.winfo_exists():
                self.upload_window.focus()
            else:
                self.upload_window = UploadWindow(master=self)
                self.bind("<<UploadClosed>>", self.close_upload_window)  # type: ignore

    def resize_images(self, event):
        assert root.current_project.image is not None
        if self.image_labels[0]:
            self.image_labels[0].configure(image=resize_image_to_label(self.image_labels[0], root.current_project.image))
        if self.image_labels[1]:
            index = len(root.current_project.temp_images) - 1
            if index >= 0:
                self.image_labels[1].configure(image=resize_image_to_label(self.image_labels[1], root.current_project.temp_images[index]))
            else:
                self.image_labels[1].configure(image=resize_image_to_label(self.image_labels[1], root.current_project.image))

    def open_filterqueue_window(self):
        if root.current_project.ready():
            if not root.current_project.image_ready():
                self.open_upload_window()
            if self.filterqueue_window is not None and self.filterqueue_window.winfo_exists():
                self.filterqueue_window.focus()
            else:
                self.filterqueue_window = FilterqueueWindow(master=self, status=root.status)

    def open_test_window(self):
        if root.current_project.ready():
            if not root.current_project.image_ready():
                self.open_upload_window()
            if self.test_window is not None and self.test_window.winfo_exists():
                self.test_window.focus()
            else:
                self.test_window = TestWindow(master=self)

    def event(self, key):
        match key:
            case "quick_test":
                def quick_test_runner():
                    root.current_project.quick_test()
                    self.open_test_window()
                threading.Thread(target=quick_test_runner, daemon=True).start()
            case "help":
                webbrowser.open_new(get_setting("help_url"))
            case "license":
                webbrowser.open_new(get_setting("license_url"))
            case "reload_images":
                self.start_action_queue_thread()
            case "save_pictures":
                threading.Thread(target=self.save_images_via_dialog, daemon=True).start()

    def save_images_via_dialog(self, last: bool = False) -> Optional[str]:
        images = getattr(root.current_project, "temp_images", None)  # type: ignore
        if not images:
            return None
        if not isinstance(images, (list, tuple)):
            return None
        if not all(isinstance(im, numpy.ndarray) for im in images):
            log.log.write(text=Error.EXPECTED_NDARRAY.value, tag="ERROR", modulename=Path(__file__).stem)
            return

        parent = tk._default_root  # type: ignore

        prepared: list[numpy.ndarray] = []
        for im in images:
            img = im
            if img.ndim == 3 and img.shape[0] in (1, 3, 4) and img.shape[-1] not in (1, 3, 4):
                img = numpy.transpose(img, (1, 2, 0))
            if img.ndim == 2:
                pass
            elif img.ndim == 3 and img.shape[-1] in (1, 3, 4):
                pass
            else:
                log.log.write(text=Error.RESIZE_IMAGE_NDIM.value, tag="ERROR", modulename=Path(__file__).stem)
                return

            if img.dtype != numpy.uint8:
                img = numpy.clip(img, 0, 255).astype(numpy.uint8, copy=False)
            prepared.append(img)

        def _img_for_encode(arr: numpy.ndarray) -> numpy.ndarray:
            if arr.ndim == 3 and arr.shape[-1] == 1:
                return arr[..., 0]
            return arr

        if len(prepared) == 1 or last:
            out_path = filedialog.asksaveasfilename(
                parent=parent, title="Save PNG",
                defaultextension=".png", filetypes=[("PNG image", "*.png")]
            )
            if not out_path:
                return None
            img_to_save = _img_for_encode(prepared[-1])
            ok, buf = cv2.imencode(".png", img_to_save, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            if not ok:
                log.log.write(text=f"{Error.SAVE_IMAGE.value}: cv2.imencode", tag="ERROR", modulename=Path(__file__).stem)
                return
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            buf.tofile(out_path)
            return out_path
        else:
            zip_path = filedialog.asksaveasfilename(
                parent=parent, title="Save ZIP with PNGs",
                defaultextension=".zip", filetypes=[("ZIP archive", "*.zip")]
            )
            if not zip_path:
                return None
            Path(zip_path).parent.mkdir(parents=True, exist_ok=True)
            with ZipFile(zip_path, mode="w", compression=ZIP_STORED) as zf:
                for i, img in enumerate(prepared, start=1):
                    img_to_save = _img_for_encode(img)
                    ok, buf = cv2.imencode(".png", img_to_save, [cv2.IMWRITE_PNG_COMPRESSION, 0])
                    if not ok:
                        log.log.write(text=f"{Error.SAVE_IMAGE.value}: #{i:04d}: cv2.imencode", tag="ERROR", modulename=Path(__file__).stem)
                        return
                    zf.writestr(f"image_{i:04d}.png", buf.tobytes())
            return zip_path
