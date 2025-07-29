import customtkinter
from ..layout import filterqueue_window
from ..utils.config_loader import get_setting, save_settings
import src.gui.state.root as root
from ..components.dropdownmenu import Dropdownmenu
from ..components.tabviewextended import TabviewExtended
import webbrowser


class MainWindow(customtkinter.CTk):
    nav_frame: Dropdownmenu | None = None
    container_frame: customtkinter.CTkFrame | customtkinter.CTkScrollableFrame | None = None

    layout_settings: dict = {
        "settings": {
            "label": {
                "font_size": 30,
                "padding": 20
            },
            "tabview": {
                "padding": 20
            }
        }
    }

    def build(self):
        self.title("Bildverabeitungs & Analysetool")
        window_size = get_setting("window_size")["main"]
        screen_coords = (int((self.winfo_screenwidth() - window_size[0]) / 2), int((self.winfo_screenheight() - window_size[1]) / 2))
        self.geometry(f"{window_size[0]}x{window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")
        self.minsize(window_size[0], window_size[1])
        self.build_nav_frame()
        self.build_container_frame()
        if root.all_keybindings is not None:
            for key in root.all_keybindings:
                self.bind_all(root.all_keybindings[key], lambda event, k=key: self.event(k))

    def build_nav_frame(self):
        self.nav_frame = Dropdownmenu(master=self)
        self.nav_frame.add("main_window_dropdownmenu_file_save", root.current_lang.get("main_window_dropdownmenu_file"), root.current_lang.get("main_window_dropdownmenu_file_save"), msg1)
        self.nav_frame.add("main_window_dropdownmenu_file_save", root.current_lang.get("main_window_dropdownmenu_file"), root.current_lang.get("main_window_dropdownmenu_file_save_all"), msg1)
        self.nav_frame.addButton("main_window_dropdownmenu_filterqueue", root.current_lang.get("main_window_dropdownmenu_filterqueue"), lambda: filterqueue_window.build(self))
        self.nav_frame.addButton("main_window_dropdownmenu_testing", root.current_lang.get("main_window_dropdownmenu_testing"), msg1)
        
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_look"), lambda: self.build_settings("main_window_settings_look"))
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_keybindings"), lambda: self.build_settings("main_window_settings_keybindings"))
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_help"), lambda: self.build_settings("main_window_settings_help"))
        self.nav_frame.add("main_window_dropdownmenu_settings", root.current_lang.get("main_window_dropdownmenu_settings"), root.current_lang.get("main_window_settings_about"), lambda: self.build_settings("main_window_settings_about"))
        self.nav_frame.pack(fill="x", side="top")
        self.nav_frame.outside_tracking(self)

    def build_container_frame(self):
        self.container_frame = customtkinter.CTkFrame(master=self, corner_radius=0)

        info_label = customtkinter.CTkLabel(master=self.container_frame, textvariable=root.current_lang.get("main_window_container_init_label"))
        info_label.place(relx=0.5, rely=0.5, anchor="center")

        self.container_frame.pack(fill="both", side="top", expand=True)

    def reset_container_frame(self):
        if self.container_frame is not None:
            for widget in self.container_frame.winfo_children():
                widget.destroy()

    def build_settings(self, tabindex: str):
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

        settings_look_lang_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=tabview.tab("main_window_settings_look"))
        settings_look_lang_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        [settings_look_lang_frame.grid_columnconfigure(i, weight=1) for i in range(5)]

        settings_look_lang_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_look_lang_frame, textvariable=root.current_lang.get("main_window_settings_look_lang_label"))
        settings_look_lang_label.grid(row=0, column=1, padx=10, pady=10)

        settings_look_lang_optionmenu: customtkinter.CTkOptionMenu = customtkinter.CTkOptionMenu(master=settings_look_lang_frame, anchor="center", values=[root.all_lang[key] for key in root.all_lang], command=self.settings_look_lang_output)
        settings_look_lang_optionmenu.grid(row=0, column=3, padx=10, pady=10)

        settings_look_darkmode_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=tabview.tab("main_window_settings_look"))
        settings_look_darkmode_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        [settings_look_darkmode_frame.grid_columnconfigure(i, weight=1) for i in range(5)]

        settings_look_darkmode_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_look_darkmode_frame, textvariable=root.current_lang.get("main_window_settings_look_darkmode_label"))
        settings_look_darkmode_label.grid(row=0, column=1, padx=10, pady=10)

        settings_look_darkmode_optionmenu: customtkinter.CTkOptionMenu = customtkinter.CTkOptionMenu(master=settings_look_darkmode_frame, anchor="center", values=["system", "dark", "light"], command=self.settings_look_darkmode_output)
        settings_look_darkmode_optionmenu.grid(row=0, column=3, padx=10, pady=10)

        settings_look_theme_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=tabview.tab("main_window_settings_look"))
        settings_look_theme_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        [settings_look_theme_frame.grid_columnconfigure(i, weight=1) for i in range(5)]

        settings_look_theme_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_look_theme_frame, textvariable=root.current_lang.get("main_window_settings_look_theme_label"))
        settings_look_theme_label.grid(row=0, column=1, padx=10, pady=10)

        settings_look_theme_optionmenu: customtkinter.CTkOptionMenu = customtkinter.CTkOptionMenu(master=settings_look_theme_frame, anchor="center", values=[key for key in root.all_styles], command=self.settings_look_theme_output)
        settings_look_theme_optionmenu.grid(row=0, column=3, padx=10, pady=10)

        settings_keybindings_save_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=tabview.tab("main_window_settings_keybindings"))
        settings_keybindings_save_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        [settings_keybindings_save_frame.grid_columnconfigure(i, weight=1) for i in range(5)]

        settings_keybindings_save_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_save_frame, textvariable=root.current_lang.get("main_window_settings_keybindings_save_label"))
        settings_keybindings_save_label.grid(row=0, column=1, padx=10, pady=10)

        settings_keybindings_save_binding_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_save_frame, fg_color=("grey", "black"), text_color=("white", "white"), corner_radius=5, padx=10, pady=10, text=root.all_keybindings["save"])
        settings_keybindings_save_binding_label.grid(row=0, column=3, padx=10, pady=10)

        settings_keybindings_quick_test_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=tabview.tab("main_window_settings_keybindings"))
        settings_keybindings_quick_test_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        [settings_keybindings_quick_test_frame.grid_columnconfigure(i, weight=1) for i in range(5)]

        settings_keybindings_quick_test_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_quick_test_frame, textvariable=root.current_lang.get("main_window_settings_keybindings_quick_test_label"))
        settings_keybindings_quick_test_label.grid(row=0, column=1, padx=10, pady=10)

        settings_keybindings_quick_test_binding_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_quick_test_frame, fg_color=("grey", "black"), text_color=("white", "white"), corner_radius=5, padx=10, pady=10, text=root.all_keybindings["quick_test"])
        settings_keybindings_quick_test_binding_label.grid(row=0, column=3, padx=10, pady=10)

        settings_keybindings_help_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(master=tabview.tab("main_window_settings_keybindings"))
        settings_keybindings_help_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        [settings_keybindings_help_frame.grid_columnconfigure(i, weight=1) for i in range(5)]

        settings_keybindings_help_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_help_frame, textvariable=root.current_lang.get("main_window_settings_keybindings_help_label"))
        settings_keybindings_help_label.grid(row=0, column=1, padx=10, pady=10)

        settings_keybindings_help_binding_label: customtkinter.CTkLabel = customtkinter.CTkLabel(master=settings_keybindings_help_frame, fg_color=("grey", "black"), text_color=("white", "white"), corner_radius=5, padx=10, pady=10, text=root.all_keybindings["help"])
        settings_keybindings_help_binding_label.grid(row=0, column=3, padx=10, pady=10)

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

def msg1():
    print("msg1")
