from typing import Callable
import customtkinter
from src.gui.components.float_entry import FloatEntry
from src.gui.state.project_file_type import Filter_Cell_Type
from src.gui.utils.config_loader import get_setting


class FilterGridCell(customtkinter.CTkFrame):

    value: customtkinter.DoubleVar | None = None
    disabled: customtkinter.BooleanVar | None = None

    enabled_disabled: bool = False
    updater: Callable
    entry: FloatEntry | None = None
    switch: customtkinter.CTkSwitch | None = None

    def __init__(self, master, value: float = 1.0, disabled: bool = False, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self._layout_settings = get_setting("components")["filter_grid_cell"]
        self.value = customtkinter.DoubleVar(value=value)
        self.disabled = customtkinter.BooleanVar(value=disabled)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)

        self.build_items()

    def build_items(self):
        assert self.value is not None and self.disabled is not None

        self.entry = FloatEntry(
            master=self,
            value=self.value.get(),
            state=("disabled" if self.disabled.get() else "normal"),
            width=50,
            justify="center"
        )
        self.entry.bind("<FocusOut>", lambda e: self.value.set(self.entry.get_float()))  # type: ignore
        self.entry.var.trace_add("write", self.update)
        self.switch = customtkinter.CTkSwitch(
            master=self, text="", variable=self.disabled, command=self._on_toggle, width=20
        )
        self.check_switch_visability()

        self.disable_cell()

    def check_switch_visability(self):
        assert self.switch is not None and self.entry is not None
        if self.enabled_disabled:
            self.entry.grid_forget()
            self.switch.grid(row=0, column=0, sticky="nswe", padx=self._layout_settings["switch"]["padding"][0:2], pady=self._layout_settings["switch"]["padding"][2:4])
        else:
            self.switch.grid_forget()
            self.entry.grid(row=0, column=0, sticky="nswe", padx=0, pady=0)

    def toogle_enable_disabled(self, boolean: bool | None = None):
        if boolean is not None:
            self.enabled_disabled = boolean
        else:
            self.enabled_disabled = not self.enabled_disabled
        self.check_switch_visability()
        self.disable_cell()

    def disable_cell(self):
        assert self.entry is not None and self.disabled is not None
        if self.enabled_disabled:
            if self.disabled.get():
                self.entry.configure(state="normal")
                self.configure(fg_color=self._layout_settings["enabled_color"])
            else:
                self.entry.configure(state="disabled")
                self.configure(fg_color=self._layout_settings["disabled_color"])
        else:
            self.entry.configure(state="normal")
            self.configure(fg_color="transparent")

    def _on_toggle(self):
        if not self.entry:
            return
        self.disable_cell()
        self.update()

    def get_cell_data(self) -> Filter_Cell_Type:
        assert self.value is not None and self.disabled is not None and self.entry is not None
        temp = self.entry.get_float()
        if temp != self.value.get():
            self.value.set(self.entry.get_float())
        return {
            "value": self.value.get(),
            "disabled": self.disabled.get()
        }

    def update(self, *args):
        self.updater()

    def set_updater(self, updater: Callable):
        self.updater = updater
