from enum import IntEnum
import uuid
import customtkinter


class _DragAndDropLockedFrame_Type(IntEnum):
    PACK = 1
    GRID = 2


class DragAndDropLockedFrame(customtkinter.CTkScrollableFrame):
    _type_pack: _DragAndDropLockedFrame_Type = _DragAndDropLockedFrame_Type.PACK
    _grid_columns: int = 1
    _items: dict[str, customtkinter.CTkFrame] = {}
    _items_order: list[str] = []
    _id_to_index: dict[str, int] = {}
    _frame_to_id: dict[customtkinter.CTkFrame, str] = {}
    _focus_old: customtkinter.CTkFrame | None = None
    _focus_dropable: customtkinter.CTkFrame | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, corner_radius=0)

    def clear(self):
        pass

    def toggle_grid(self, columns: int):
        self._type_pack = _DragAndDropLockedFrame_Type.GRID

    def add(self, frame: customtkinter.CTkFrame):
        id_ = str(uuid.uuid4())
        self._items[id_] = frame
        self._items_order.append(id_)
        self._frame_to_id[frame] = id_
        self._id_to_index[id_] = len(self._items_order) - 1
        frame.bind("<Button-1>", self.drag)
        frame.bind("<ButtonRelease-1>", self.drop)
        frame.bind("<B1-Motion>", self.dropable)

    def get_frames(self) -> list[customtkinter.CTkFrame]:
        return [self._items[i] for i in self._items_order]

    def hide(self) -> None:
        if self._type_pack == _DragAndDropLockedFrame_Type.PACK:
            for f in self.get_frames():
                f.pack_forget()
        elif self._type_pack == _DragAndDropLockedFrame_Type.GRID:
            for f in self.get_frames():
                f.grid_forget()

    def show(self):
        if self._type_pack == _DragAndDropLockedFrame_Type.PACK:
            for f in self.get_frames():
                f.pack(fill="x")
            return

        if self._type_pack == _DragAndDropLockedFrame_Type.GRID:
            cols = max(1, int(self._grid_columns))
            for c in range(cols):
                self.grid_columnconfigure(c, weight=1)

            row = column = 0
            for idx, f in enumerate(self.get_frames()):
                f.grid(row=row, column=column, sticky="nsew")
                self.grid_rowconfigure(row, weight=1)

                column += 1
                if column >= cols:
                    column = 0
                    row += 1

    def drag(self, event) -> None:
        self.clear_focus()
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if widget is None:
            return
        master = getattr(widget, "master", None)
        if isinstance(master, customtkinter.CTkFrame) and master.master == self:
            self._focus_old = master
            self._focus_dropable = None
            self._focus_old.configure(border_color="orange")

    def drop(self, event):
        if self._focus_old is not None and self._focus_dropable is not None:
            self.switch_frames(self._focus_old, self._focus_dropable)
            self._focus_old = None
            self._focus_dropable = None
            self.clear_focus()

    def dropable(self, event) -> None:
        widget_pre = event.widget.winfo_containing(event.x_root, event.y_root)
        if widget_pre is None:
            return
        widget = getattr(widget_pre, "master", None)

        if self._focus_old is None:
            return

        if widget is not self._focus_old and isinstance(widget, customtkinter.CTkFrame) and widget.master == self:
            self._focus_dropable = widget
            self._focus_dropable.configure(border_color="green")
            self.clear_focus()
        else:
            self._focus_dropable = None
            self.clear_focus()

    def clear_focus(self):
        for child in self.winfo_children():
            if child is not self._focus_old and child is not self._focus_dropable:
                if isinstance(child, customtkinter.CTkFrame):
                    child.configure(border_color="grey")

    def get_id_by_frame(self, frame: customtkinter.CTkFrame) -> str | None:
        return self._frame_to_id.get(frame)

    def switch_frames(self, frame1: customtkinter.CTkFrame, frame2: customtkinter.CTkFrame):
        frame1_id = self.get_id_by_frame(frame1)
        frame2_id = self.get_id_by_frame(frame2)
        if frame1_id is None or frame2_id is None or frame1_id == frame2_id:
            return
        i1 = self._id_to_index[frame1_id]
        i2 = self._id_to_index[frame2_id]
        self._items_order[i1], self._items_order[i2] = self._items_order[i2], self._items_order[i1]
        self._id_to_index[frame1_id], self._id_to_index[frame2_id] = i2, i1
        self.hide()
        self.show()
