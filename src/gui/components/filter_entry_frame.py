import customtkinter

from src.gui.state.project_file_type import Filter_Type


class FilterEntryFrame(customtkinter.CTkFrame):
    filter: Filter_Type | str | None = None

    name_label: customtkinter.CTkLabel | None = None
    size_label: customtkinter.CTkLabel | None = None
    type_label: customtkinter.CTkLabel | None = None
    edit_button: customtkinter.CTkButton | None = None
    delete_button: customtkinter.CTkButton | None = None

    def __init__(self, master, filter, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self.filter = filter
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if type(self.filter) is dict:
            self.name_label = customtkinter.CTkLabel(master=self, text=self.filter["name"])
            self.type_label = customtkinter.CTkLabel(master=self, text=self.filter["settings"]["type"])
            self.type_label.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")
            self.size_label = customtkinter.CTkLabel(master=self, text=str(self.filter["settings"]["size"]))
            self.size_label.grid(row=0, column=2, padx=10, pady=10, sticky="nswe")
        elif type(self.filter) is str:
            self.name_label = customtkinter.CTkLabel(master=self, text=self.filter)
        else:
            self.name_label = customtkinter.CTkLabel(master=self, text="None")
        self.name_label.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")

        self.delete_button = customtkinter.CTkButton(master=self, text="Delete")
        self.delete_button.grid(row=0, column=3, padx=10, pady=10, sticky="nswe")

        self.edit_button = customtkinter.CTkButton(master=self, text="Edit")
        self.edit_button.grid(row=0, column=4, padx=10, pady=10, sticky="nswe")

    def delete(self):
        self.delete()

    def get_info(self) -> Filter_Type | str | None:
        return self.filter

    def open_filter_window(self):
        pass
