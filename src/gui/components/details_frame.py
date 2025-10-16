from pathlib import Path
import customtkinter as ctk
import src.gui.utils.logger as log
from src.gui.state.error import Error


class DetailsFrame(ctk.CTkFrame):

    def __init__(
        self,
        master,
        summary: str = "Details",
        open: bool = False,
        padding=(8, 8),
        header_padding=(8, 8),
        header_fg_color=None,
        hover: bool = True,
        command=None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self._is_open = bool(open)
        self._command = command

        if isinstance(padding, int):
            self._padx = self._pady = padding
        else:
            self._padx, self._pady = padding

        if isinstance(header_padding, int):
            self._hpadx = self._hpady = header_padding
        else:
            self._hpadx, self._hpady = header_padding

        self.header = ctk.CTkButton(
            self,
            fg_color=header_fg_color,
            hover=hover,
            text=self._format_summary_text(summary),
            anchor="w",
            command=self.toggle,
            corner_radius=0,
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=self._hpadx, pady=self._hpady)
        self.grid_columnconfigure(0, weight=1)

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid_columnconfigure(0, weight=1)

        if self._is_open:
            self.open()
        else:
            self.close()

    @property
    def content(self):
        return self._content

    def add(self, widget, **grid_kwargs):
        if widget.winfo_parent() != str(self._content):
            log.log.write(text=Error.DETAILSFRAME_SET_MASTER.value, tag="ERROR", modulename=Path(__file__).stem)
            return

        if "row" not in grid_kwargs and "column" not in grid_kwargs:
            next_row = self._content.grid_size()[1]
            grid_kwargs.setdefault("row", next_row)
            grid_kwargs.setdefault("column", 0)
            grid_kwargs.setdefault("sticky", "ew")

        widget.grid(**grid_kwargs)

    def open(self):
        self._is_open = True
        self._content.grid(row=1, column=0, sticky="ew", padx=self._padx, pady=self._pady)
        self._refresh_header()
        if self._command:
            self._command(self._is_open)

    def close(self):
        self._is_open = False
        self._content.grid_forget()
        self._refresh_header()
        if self._command:
            self._command(self._is_open)

    def toggle(self):
        if self._is_open:
            self.close()
        else:
            self.open()

    def is_open(self) -> bool:
        return self._is_open

    def set_summary(self, text: str):
        self.header.configure(text=self._format_summary_text(text))

    def set_padding(self, padding):
        if isinstance(padding, int):
            self._padx = self._pady = padding
        else:
            self._padx, self._pady = padding
        if self._is_open:
            self._content.grid_configure(padx=self._padx, pady=self._pady)

    def set_header_padding(self, padding):
        if isinstance(padding, int):
            self._hpadx = self._hpady = padding
        else:
            self._hpadx, self._hpady = padding
        self.header.grid_configure(padx=self._hpadx, pady=self._hpady)

    def _format_summary_text(self, summary_text: str) -> str:
        arrow = "▾" if self._is_open else "▸"
        return f"{arrow}  {summary_text}"

    def _refresh_header(self):
        current = self.header.cget("text")
        if "  " in current:
            _, text = current.split("  ", 1)
        else:
            text = current
        self.header.configure(text=self._format_summary_text(text))
