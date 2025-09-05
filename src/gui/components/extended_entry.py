import customtkinter
import src.gui.state.root as root


class ExtendedEntry(customtkinter.CTkEntry):

    default_word: customtkinter.StringVar | None = None
    _last_valid: str = ""
    restore_timer: int = 3000
    allowed_chars: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_0123456789"
    _empty_timer: str | None = None
    id: str | None = None
    _var: customtkinter.StringVar | None = None

    def __init__(self, master, default_word: customtkinter.StringVar, id: str | None, tracker_var: customtkinter.StringVar, **kwargs):
        self.id = id
        self._var = tracker_var
        self.default_word = default_word
        self._last_valid = tracker_var.get()
        vcmd = (master.register(self._on_validate), "%P")
        super().__init__(master, textvariable=self._var,
                         validate="key", validatecommand=vcmd, **kwargs)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_validate(self, P: str) -> bool:
        self._cancel_empty_timer()
        if P == "":
            self._schedule_empty_restore()
            self.bell()
            return True
        for char in P:
            if char not in self.allowed_chars:
                return False
        if self.id is not None:
            new_name = root.current_project.get_filterid_by_name(P)
            if not (new_name is None or new_name is self.id):
                return False
        self._last_valid = P
        return True

    def _schedule_empty_restore(self):
        self._empty_timer = self.after(self.restore_timer, self._restore_last_valid)

    def _cancel_empty_timer(self):
        if self._empty_timer is not None:
            try:
                self.after_cancel(self._empty_timer)
            except Exception:
                pass
            self._empty_timer = None

    def _restore_last_valid(self):
        assert self._var is not None
        self._empty_timer = None
        self.configure(validate="none")
        self._var.set(self._last_valid)
        self.configure(validate="key")

    def _on_focus_out(self, _e=None):
        assert self._var is not None
        if self._var.get() == "":
            self._restore_last_valid()
        if self._on_validate(self._var.get()):
            self._last_valid = self._var.get()
