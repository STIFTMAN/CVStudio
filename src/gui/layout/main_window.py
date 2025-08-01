from typing import Callable
import customtkinter
from ..layout.filterqueue_window import FilterqueueWindow
from ..utils.config_loader import get_setting, save_settings
import src.gui.state.root as root
from ..components.dropdownmenu import Dropdownmenu
from ..components.tabviewextended import TabviewExtended
import webbrowser
import re
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import cv2
from PIL import Image


class MainWindow(TkinterDnD.Tk):
    nav_frame: Dropdownmenu | None = None
    container_frame: customtkinter.CTkFrame | customtkinter.CTkScrollableFrame | None = None
    filterqueue_window: FilterqueueWindow | None = None

    layout_settings: dict = {}

    image_label = None

    def __init__(self):
        super().__init__()

    def build(self):
        self.title(get_setting("name"))
        self.iconbitmap("src/assets/favicon.ico")
        window_size = get_setting("window_size")["main"]
        screen_coords = (int((self.winfo_screenwidth() - window_size[0]) / 2), int((self.winfo_screenheight() - window_size[1]) / 2))
        self.geometry(f"{window_size[0]}x{window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.minsize(window_size[0], window_size[1])
        self.layout_settings = get_setting("styles")["main_window"]
        self.build_nav_frame()
        self.build_container_frame()
        if root.all_keybindings is not None:
            for key in root.all_keybindings:
                self.bind_all(root.all_keybindings[key], lambda event, k=key: self.event(k))
        print("Version: ", root.version)

    def build_nav_frame(self):
        self.nav_frame = Dropdownmenu(master=self)
        self.nav_frame.add("main_window_dropdownmenu_file_save", root.current_lang.get("main_window_dropdownmenu_file"), root.current_lang.get("main_window_dropdownmenu_file_save"), msg1)
        self.nav_frame.add("main_window_dropdownmenu_file_save", root.current_lang.get("main_window_dropdownmenu_file"), root.current_lang.get("main_window_dropdownmenu_file_save_all"), msg1)
        self.nav_frame.addButton("main_window_dropdownmenu_filterqueue", root.current_lang.get("main_window_dropdownmenu_filterqueue"), self.open_filterqueue_window)
        self.nav_frame.addButton("main_window_dropdownmenu_testing", root.current_lang.get("main_window_dropdownmenu_testing"), msg1)

        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_look"), lambda: self.build_settings("main_window_settings_look"))
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_keybindings"), lambda: self.build_settings("main_window_settings_keybindings"))
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_help"), lambda: self.build_settings("main_window_settings_help"))
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_about"), lambda: self.build_settings("main_window_settings_about"))
        self.nav_frame.pack(fill="x", side="top")
        self.nav_frame.outside_tracking(self)

    def build_container_frame(self):
        self.container_frame = customtkinter.CTkFrame(master=self, corner_radius=0)

        self.image_label = customtkinter.CTkLabel(master=self.container_frame, textvariable=root.current_lang.get("main_window_container_init_label"))
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        self.image_label.drop_target_register(DND_FILES)
        self.image_label.dnd_bind('<<Drop>>', self.on_drop)

        self.container_frame.pack(fill="both", side="top", expand=True)

    def on_drop(self, event):
        filepath = event.data.strip("{}")
        if os.path.isfile(filepath) and filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            img_cv = cv2.imread(filepath)
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)

            # Originalgröße holen
            h, w = img_cv.shape[:2]

            # In PIL konvertieren
            img_pil = Image.fromarray(img_cv)

            # Zielgröße für das Label
            target_w, target_h = 600, 400
            scale = min(target_w / w, target_h / h)  # Aspect Ratio beibehalten
            new_w, new_h = int(w * scale), int(h * scale)

            # CTkImage mit skaliertem Bild
            img_ctk = customtkinter.CTkImage(light_image=img_pil, size=(new_w, new_h))

            # Bild anzeigen
            self.image_label.configure(image=img_ctk, text="")
            self.image_label.image = img_ctk  # Referenz halten!

    def reset_container_frame(self):
        if self.container_frame is not None:
            for widget in self.container_frame.winfo_children():
                widget.destroy()

    def build_settings(self, tabindex: str):
        assert root.all_keybindings is not None
        self.reset_container_frame()
        headline_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=self.container_frame, textvariable=root.current_lang.get("main_window_dropdownmenu_settings"), font=("Roboto", self.layout_settings["settings"]["label"]["font_size"]))
        headline_label.pack(fill="x", side="top", padx=self.layout_settings["settings"]["label"]["padding"], pady=(self.layout_settings["settings"]["label"]["padding"], 0))

        tabview: TabviewExtended = TabviewExtended(master=self.container_frame)
        tabview.pack(fill="both", side="top", expand=True, padx=self.layout_settings["settings"]["tabview"]["padding"], pady=self.layout_settings["settings"]["tabview"]["padding"])

        tabview.add_tab("main_window_settings_look", root.current_lang.get("main_window_settings_look"))
        tabview.add_tab("main_window_settings_keybindings", root.current_lang.get("main_window_settings_keybindings"))
        tabview.add_tab("main_window_settings_help", root.current_lang.get("main_window_settings_help"))
        tabview.add_tab("main_window_settings_about", root.current_lang.get("main_window_settings_about"))
        tabview.set(tabindex)
        tabview.tab("main_window_settings_look").grid_columnconfigure(0, weight=1)
        tabview.tab("main_window_settings_keybindings").grid_columnconfigure(0, weight=1)
        tabview.tab("main_window_settings_help").grid_columnconfigure(0, weight=1)
        tabview.tab("main_window_settings_help").grid_rowconfigure(0, weight=1)
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
            ("main_window_settings_keybindings_save_label", "save"),
            ("main_window_settings_keybindings_quick_test_label", "quick_test"),
            ("main_window_settings_keybindings_help_label", "help"),
            ("main_window_settings_keybindings_license_label", "license")
        ]
        for key in range(len(settings_keybindings_keys)):

            settings_keybindings_temp_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=tabview.tab("main_window_settings_keybindings"))
            settings_keybindings_temp_frame.grid(row=key, column=0, padx=self.layout_settings["settings"]["keybindings"]["frame"]["padding"], pady=self.layout_settings["settings"]["keybindings"]["frame"]["padding"], sticky="nsew")
            [settings_keybindings_temp_frame.grid_columnconfigure(i, weight=1) for i in range(3)]

            settings_keybindings_temp_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_temp_frame, width=self.layout_settings["settings"]["keybindings"]["label"]["width"], anchor="w", textvariable=root.current_lang.get(settings_keybindings_keys[key][0]))
            settings_keybindings_temp_label.grid(row=0, column=1, padx=self.layout_settings["settings"]["keybindings"]["label"]["padding"], pady=self.layout_settings["settings"]["keybindings"]["label"]["padding"])

            settings_keybindings_temp_binding_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_temp_frame, width=self.layout_settings["settings"]["keybindings"]["binding_label"]["width"], fg_color=("grey", "black"), text_color=("white", "white"), corner_radius=5, text=re.sub(r"[<>]", "", root.all_keybindings[settings_keybindings_keys[key][1]]).replace("Control", "Ctrl").replace("-", " + "))
            settings_keybindings_temp_binding_label.grid(row=0, column=3, padx=self.layout_settings["settings"]["keybindings"]["binding_label"]["padding"], pady=self.layout_settings["settings"]["keybindings"]["binding_label"]["padding"])

        settings_help_frame: customtkinter.CTkScrollableFrame = customtkinter.CTkScrollableFrame(master=tabview.tab("main_window_settings_help"), fg_color="transparent")
        settings_help_frame.grid(row=0, column=0, sticky="nswe", padx=self.layout_settings["settings"]["help"]["frame"]["padding"], pady=self.layout_settings["settings"]["help"]["frame"]["padding"])
        settings_help_frame.grid_columnconfigure(0, weight=1)


# WIRD SPÄTER GEMACHT
        settings_help_keys: list[str | customtkinter.StringVar] = [
            root.current_lang.get("main_window_settings_help_label_1")
        ]

        for key in range(len(settings_help_keys)):
            if isinstance(settings_help_keys[key], customtkinter.StringVar):
                settings_help_temp_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_help_frame, padx=self.layout_settings["settings"]["help"]["label"]["padding_inline"][0], pady=self.layout_settings["settings"]["help"]["label"]["padding_inline"][1], anchor="w", wraplength=800, justify="left", textvariable=settings_help_keys[key])
            else:
                settings_help_temp_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_help_frame, wraplength=800, justify="left", padx=self.layout_settings["settings"]["help"]["label"]["padding_inline"][0], pady=self.layout_settings["settings"]["help"]["label"]["padding_inline"][1], anchor="w", text=settings_help_keys[key])
            settings_help_temp_label.grid(row=key, column=0, padx=self.layout_settings["settings"]["help"]["label"]["padding"][0], pady=self.layout_settings["settings"]["help"]["label"]["padding"][1], sticky="w")

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
                settings_about_temp_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=tabview.tab("main_window_settings_about"), padx=self.layout_settings["settings"]["about"]["label"]["padding_inline"][0], pady=self.layout_settings["settings"]["about"]["label"]["padding_inline"][1], anchor="w", wraplength=800, justify="left", textvariable=settings_about_keys[key])
            else:
                settings_about_temp_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=tabview.tab("main_window_settings_about"), wraplength=800, justify="left", padx=self.layout_settings["settings"]["about"]["label"]["padding_inline"][0], pady=self.layout_settings["settings"]["about"]["label"]["padding_inline"][1], anchor="w", text=settings_about_keys[key])
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
            restart()
    
    def open_filterqueue_window(self):
        if self.filterqueue_window is not None and self.filterqueue_window.winfo_exists():
            self.filterqueue_window.focus()
        else:
            self.filterqueue_window = FilterqueueWindow(master=self)

# WIRD SPÄTER GEMACHT
    def event(self, key):
        print("Event | " + key)
        match key:
            case "save":
                pass
            case "quick_test":
                pass
            case "help":
                webbrowser.open_new(get_setting("help_url"))
            case "license":
                webbrowser.open_new(get_setting("license_url"))


def msg1():
    print("msg1")
