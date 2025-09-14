import re
from typing import Callable
import customtkinter as ctk
from src.gui.utils.config_loader import get_setting
import src.gui.state.root as root


class ComboBoxExtended(ctk.CTkFrame):
    _all_values: list[tuple[str, str]] = []
    _filtered: list[tuple[str, str]] = []
    _command: Callable | None = None
    _selection_index: int = -1
    _is_open: bool = False
    _entry: ctk.CTkEntry | None = None
    _btn: ctk.CTkButton | None = None
    _popup: ctk.CTkToplevel | None = None
    _list_frame: ctk.CTkScrollableFrame | None = None
    _item_widgets: list[ctk.CTkButton | ctk.CTkLabel] = []
    _selected_id: str = ""
    _layout_settings: dict = {}

    def __init__(self, master, values: list[tuple[str, str]] = [], command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._layout_settings = get_setting("components")["comboboxextended"]
        self._all_values = values
        self._all_values.sort()
        self._filtered = self._all_values
        self._command = command
        self._max_visible = self._layout_settings["max_visible"]
        self._selection_index = -1
        self._is_open = False
        self._popup = None
        self._list_frame = None
        self._item_widgets = []
        self._entry = ctk.CTkEntry(self, placeholder_text=self._layout_settings["placeholder_text"], width=self._layout_settings["width"])
        self._entry.grid(row=0, column=0, sticky="ew")
        self.grid_columnconfigure(0, weight=1)
        self._btn = ctk.CTkButton(self, text="▼", width=self._layout_settings["open_button"]["width"], command=self.toggle_dropdown)
        self._btn.grid(row=0, column=1, pady=self._layout_settings["open_button"]["padding"][2:4], padx=self._layout_settings["open_button"]["padding"][0:2])

        self._entry.bind("<KeyRelease>", self._on_key_release, add=True)
        self._entry.bind("<KeyPress>", self._on_key_press, add=True)
        self._entry.bind("<FocusOut>", self._maybe_close_on_focus_out, add=True)
        self.bind("<Configure>", lambda e: self._reposition_popup(), add=True)
        try:
            self.winfo_toplevel().bind("<Configure>", lambda e: self._reposition_popup(), add=True)
        except Exception:
            pass

        self._refresh_list()

    def add_value(self, value: tuple[str, str]):
        self._all_values.append(value)
        self._all_values = list(set(self._all_values))
        self._all_values.sort()

    def get(self) -> str:
        return self._entry.get() if self._entry else ""

    def set(self, value: tuple[str, str]):
        if self._entry:
            self._entry.delete(0, "end")
            self._entry.insert(0, value[0])
            self._selected_id = value[1]
            self._filter_and_show()

    def set_values(self, values: list[tuple[str, str]] = []):
        self._all_values = values
        self._all_values.sort()
        self._filter_and_show()

    def set_updater(self, updater: Callable):
        self._command = updater

    def toggle_dropdown(self):
        if self._is_open:
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        if self._is_open:
            self._rebuild_list()
            self._reposition_popup()
            return
        self._popup = ctk.CTkToplevel(self)
        self._popup.grid_columnconfigure(0, weight=1)
        self._popup.grid_rowconfigure(0, weight=1)
        self._popup.overrideredirect(True)
        self._popup.transient(self.winfo_toplevel())
        self._popup.attributes("-topmost", True)
        self._popup.bind("<FocusOut>", self._maybe_close_on_focus_out, add="+")
        assert self._entry is not None
        self._list_frame = ctk.CTkScrollableFrame(self._popup, width=self._entry.winfo_width(), corner_radius=0)
        try:
            self._list_frame._scrollbar.grid_remove()
            self._list_frame.after_idle(lambda: self._list_frame._scrollbar.grid_remove())  # type: ignore
        except Exception:
            pass
        self._list_frame.grid_columnconfigure(0, weight=1)
        self._list_frame.grid(column=0, row=0, sticky="nswe")

        self._rebuild_list()
        self._reposition_popup()
        self._is_open = True

    def _close_popup(self):
        self._is_open = False
        self._selection_index = -1
        if self._popup and self._popup.winfo_exists():
            try:
                self._popup.destroy()
            except Exception:
                pass
        self._popup = None
        self._list_frame = None
        self._item_widgets = []

    def _maybe_close_on_focus_out(self, _event=None):
        if self._popup and self._popup.winfo_exists():
            focus = self.focus_get()
            if focus and (focus == self._popup or str(focus).startswith(str(self._popup))):
                return
        self._close_popup()

    def _reposition_popup(self):
        if not (self._popup and self._popup.winfo_exists()):
            return
        try:
            assert self._entry is not None and self._btn is not None
            diff_y = self._layout_settings["popup"]["diff_y"]
            diff_w = self._layout_settings["popup"]["diff_w"]
            x = self._entry.winfo_rootx()
            y = self._entry.winfo_rooty() + self._entry.winfo_height() + diff_y
            w = self._entry.winfo_width() + self._btn.winfo_width() + diff_w
            item_h = self._layout_settings["popup"]["item_height"]
            visible = min(len(self._filtered), self._max_visible)
            h = max(item_h * visible, item_h)
            self._popup.geometry(f"{w}x{int(h)}+{int(x)}+{int(y)}")
        except Exception:
            pass

    def _sanitize(self, text: str) -> str:
        return re.sub(r"[^A-Za-z0-9\-_]", "", text)

    def _filter_and_show(self):
        assert self._entry is not None
        needle = self._sanitize(self.get())
        if needle != self.get():
            self._entry.delete(0, "end")
            self._entry.insert(0, needle)

        self._filtered = [v for v in self._all_values if v[0].lower().startswith(needle.lower())] if needle else self._all_values[:]
        self._selection_index = -1
        if self._is_open:
            self._rebuild_list()
            self._reposition_popup()

    def _refresh_list(self):
        self._filtered = self._all_values[:]
        if self._is_open:
            self._rebuild_list()
            self._reposition_popup()

    def _rebuild_list(self):
        if not (self._popup and self._popup.winfo_exists() and self._list_frame):
            return
        for i, w in enumerate(self._item_widgets):
            try:
                self._list_frame.grid_rowconfigure(i, weight=0)
                w.destroy()
            except Exception:
                pass
        self._item_widgets = []

        data = self._filtered
        if not data:
            self._list_frame.grid_rowconfigure(0, weight=1)
            lbl = ctk.CTkLabel(self._list_frame, textvariable=root.current_lang.get("components_comboboxextendet_no_result"), height=self._layout_settings["popup"]["item_height"])
            lbl.grid(row=0, column=0, sticky="nswe")
            self._item_widgets.append(lbl)
            return

        for i, val in enumerate(data):
            self._list_frame.grid_rowconfigure(i, weight=1)
            b = ctk.CTkButton(self._list_frame, text=f"{val[0]} # {val[1][0:8]}...", anchor="w", height=self._layout_settings["popup"]["item_height"], command=lambda v=val: self._select_value(v), corner_radius=0, border_spacing=1, border_width=1)
            b.grid(row=i, column=0, sticky="nswe")
            self._item_widgets.append(b)

    def _select_value(self, value: tuple[str, str]):
        self.set(value)
        self._close_popup()
        if callable(self._command):
            try:
                self._command(value)
            except Exception:
                pass

    def _on_key_press(self, event):
        allowed_keys = {
            "BackSpace", "Delete", "Left", "Right", "Home", "End",
            "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R"
        }
        if event.keysym in allowed_keys:
            return
        if len(event.char or "") == 1 and not re.match(r"[A-Za-z0-9\-_]", event.char):
            return "break"

    def _on_key_release(self, event):
        if event and event.keysym in {"Escape"}:
            self._close_popup()
            return
        if event and event.keysym in {"Up", "Down"}:
            if not self._is_open:
                self._open_popup()
            self._move_selection(-1 if event.keysym == "Up" else +1)
            return
        if event and event.keysym in {"Return", "KP_Enter"}:
            if self._is_open and 0 <= self._selection_index < len(self._filtered):
                self._select_value(self._filtered[self._selection_index])
            else:
                if callable(self._command):
                    self._command(self.get())
            return
        self._filter_and_show()
        if not self._is_open:
            self._open_popup()
        assert self._entry is not None
        self._entry.focus_force()

    def _move_selection(self, delta: int):
        if not self._filtered:
            return
        visible = self._filtered[: self._max_visible] if self._max_visible else self._filtered
        if not visible:
            return
        if self._selection_index == -1:
            self._selection_index = 0 if delta > 0 else len(visible) - 1
        else:
            self._selection_index = (self._selection_index + delta) % len(visible)
