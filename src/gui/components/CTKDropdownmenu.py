import customtkinter
from ..state.root import app


class CTKDropdownmenu(customtkinter.CTkFrame):
    menu: dict[str, list[tuple[str, callable]]] = {}
    menu_sub_widgets: dict[str, list[tuple[str, customtkinter.CTkButton]]] = {}
    menu_visible: None | str = None
    menu_top_widgets: dict[str, dict[str, customtkinter.CTkButton | customtkinter.CTkFrame]] = {}

    grid_size: int = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, corner_radius=0)

    def outside_tracking(self, root: customtkinter.CTk):
        root.bind("<Button-1>", self.click_outside)
        self.bind(
            "<Configure>",
            lambda event: self.after(50, self.resize)
        )

    def resize(self):
        if self.menu_visible is not None and self.menu_top_widgets[self.menu_visible]["frame"].winfo_ismapped():
            self.show_menu(self.menu_visible)

    def add(self, menu_name: str, item_name: str, item_command: callable):
        if menu_name not in self.menu:
            self.menu[menu_name] = []
            self.menu_top_widgets[menu_name] = {}
            self.menu_sub_widgets[menu_name] = []
            self.menu_top_widgets[menu_name]["frame"] = None
            self.menu_top_widgets[menu_name]["button"] = customtkinter.CTkButton(self, text=menu_name, corner_radius=0, command=lambda: self.toggle_menu(menu_name))
            self.menu_top_widgets[menu_name]["button"].grid(row=0, column=self.grid_size, sticky="nswe", padx=1)
            self.grid_columnconfigure(self.grid_size, weight=1)
            self.grid_size += 1
        self.menu[menu_name].append((item_name, item_command))

    def addButton(self, menu_name: str, item_command: callable):
        if menu_name not in self.menu:
            self.menu[menu_name] = []
            self.menu_top_widgets[menu_name] = {}
            self.menu_sub_widgets[menu_name] = []
            self.menu_top_widgets[menu_name]["button"] = customtkinter.CTkButton(self, text=menu_name, corner_radius=0, command=item_command)
            self.menu_top_widgets[menu_name]["button"].grid(row=0, column=self.grid_size, sticky="nswe", padx=1)
            self.grid_columnconfigure(self.grid_size, weight=1)
            self.grid_size += 1

    def toggle_menu(self, menu_name: str):
        if self.menu_visible == menu_name:
            self.hide_menu(menu_name)
            self.menu_visible = None
            return
        self.menu_visible = menu_name
        self.show_menu(menu_name)

    def show_menu(self, menu_name: str):
        frame_x = self.menu_top_widgets[menu_name]["button"].winfo_x()
        frame_y = self.menu_top_widgets[menu_name]["button"].winfo_y() + self.menu_top_widgets[menu_name]["button"].winfo_height() + 2
        frame_width = self.menu_top_widgets[menu_name]["button"].winfo_width()
        frame_height = self.menu_top_widgets[menu_name]["button"].winfo_height()
        self.hide_menu(menu_name)
        self.menu_top_widgets[menu_name]["frame"] = customtkinter.CTkFrame(app, corner_radius=0, width=frame_width, height=frame_height*len(self.menu[menu_name]))
        for entry in self.menu[menu_name]:
            btn = customtkinter.CTkButton(self.menu_top_widgets[menu_name]["frame"], text=entry[0], corner_radius=0, width=frame_width, command=lambda: [entry[1](), self.hide_menu_all()])
            btn.pack(fill="both", expand=True)
        self.menu_top_widgets[menu_name]["frame"].place(x=frame_x, y=frame_y)
        self.menu_top_widgets[menu_name]["frame"].update_idletasks()

    def hide_menu(self, menu_name: str):
        if "frame" in self.menu_top_widgets[menu_name] and self.menu_top_widgets[menu_name]["frame"] is not None:
            self.menu_top_widgets[menu_name]["frame"].destroy()
            self.menu_top_widgets[menu_name]["frame"] = None

    def hide_menu_all(self):
        for key in self.menu_top_widgets:
            self.hide_menu(key)
        self.menu_visible = None

    def click_outside(self, event):
        if self.menu_visible is not None:
            widget = str(event.widget)
            for key in self.menu_top_widgets:
                if key != self.menu_visible:
                    self.hide_menu(key)
            if not widget.startswith(str(self.menu_top_widgets[self.menu_visible]["frame"])) and not widget.startswith(str(self.menu_top_widgets[self.menu_visible]["button"])):
                self.hide_menu_all()
