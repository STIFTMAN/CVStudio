from enum import IntEnum
import customtkinter
import uuid


class DragAndDropLockedFrame_Type(IntEnum):
    PACK = 1
    GRID = 2


class DragAndDropLockedFrame(customtkinter.CTkScrollableFrame):

    type_pack: DragAndDropLockedFrame_Type = DragAndDropLockedFrame_Type.PACK

    grid_columns: int = 1

    items: dict[str, customtkinter.CTkFrame] = {}
    items_order: list[str] = []

    focus_old: customtkinter.CTkFrame | None = None
    focus_dropable: customtkinter.CTkFrame | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, corner_radius=0)

    def add(self, frame: customtkinter.CTkFrame):
        id = str(uuid.uuid4())
        self.items[id] = frame
        self.items_order.append(id)

        frame.bind("<Button-1>", lambda event: self.drag(event))
        frame.bind("<ButtonRelease-1>", lambda event: self.drop(event))
        frame.bind("<B1-Motion>", lambda event: self.dropable(event))

    def get_frames(self) -> list[customtkinter.CTkFrame]:
        return [self.items[i] for i in self.items_order]

    def hide(self) -> None:
        if self.type_pack == DragAndDropLockedFrame_Type.PACK:
            [i.pack_forget() for i in self.get_frames()]
        elif self.type_pack == DragAndDropLockedFrame_Type.GRID:
            [i.grid_forget() for i in self.get_frames()]

    def show(self):
        if self.type_pack == DragAndDropLockedFrame_Type.PACK:
            [i.pack(fill="x") for i in self.get_frames()]
        elif self.type_pack == DragAndDropLockedFrame_Type.GRID:
            column = 0
            row = 0
            self.grid_rowconfigure(0, weight=1)
            for i in self.get_frames():
                i.grid(row=row, column=column, sticky="nsew")
                self.grid_columnconfigure(column, weight=1)
                column += 1
                if column % self.grid_columns == 0:
                    column = 0
                    row += 1
                    self.grid_rowconfigure(row, weight=1)

    def drag(self, event) -> None:
        self.clear_focus()
        widget = event.widget.winfo_containing(event.x_root, event.y_root).master
        if isinstance(widget, customtkinter.CTkFrame) and widget.master == self:
            self.focus_old = widget
            self.focus_dropable = None
            self.focus_old.configure(border_color="orange")

    def drop(self, event):
        if self.focus_old is not None and self.focus_dropable is not None:
            self.switch_frames(self.focus_old, self.focus_dropable)
            self.focus_old = None
            self.focus_dropable = None
            self.clear_focus()

    def dropable(self, event) -> None:
        widgetpre = event.widget.winfo_containing(event.x_root, event.y_root)
        if widgetpre is None:
            return
        widget = widgetpre.master
        if self.focus_old is not None:
            if widget != self.focus_old:
                if isinstance(widget, customtkinter.CTkFrame) and widget.master == self:
                    self.focus_dropable = widget
                    self.focus_dropable.configure(border_color="green")
                    self.clear_focus()
            else:
                self.focus_dropable = None
                self.clear_focus()

    def clear_focus(self):
        for child in self.winfo_children():
            if child != self.focus_old and child != self.focus_dropable:
                assert type(child) is customtkinter.CTkFrame
                child.configure(border_color="grey")

    def get_id_by_frame(self, frame: customtkinter.CTkFrame) -> str | None:
        for i in self.items:
            if self.items[i] == frame:
                return i
        return None

    def switch_frames(self, frame1: customtkinter.CTkFrame, frame2: customtkinter.CTkFrame):
        frame1_id = self.get_id_by_frame(frame1)
        frame2_id = self.get_id_by_frame(frame2)
        if frame1_id is not None and frame2_id is not None:
            temp_frame1_id_index = self.items_order.index(frame1_id)
            temp_frame2_id_index = self.items_order.index(frame2_id)
            self.items_order[temp_frame1_id_index] = frame2_id
            self.items_order[temp_frame2_id_index] = frame1_id
        self.hide()
        self.show()
