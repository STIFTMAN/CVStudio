import customtkinter


class TabviewExtended(customtkinter.CTkTabview):

    text_list: dict[str, customtkinter.StringVar] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def change(self, *args):
        for key in self.text_list:
            if self._segmented_button._buttons_dict[key].winfo_exists():
                self._segmented_button._buttons_dict[key].configure(text=self.text_list[key].get())

    def add_tab(self, id: str, text: customtkinter.StringVar):
        text.trace_add("write", self.change)
        self.text_list[id] = text
        self.add(id)
        self._segmented_button._buttons_dict[id].configure(text=text.get())
