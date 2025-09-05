import customtkinter as ctk


class IntEntry(ctk.CTkEntry):
    allowed: set[int] | None = None

    _value_range: tuple[int | None, int | None] = (None, None)
    _last_valid: int = 0
    _empty_timer: str | None = None
    int_var: ctk.IntVar | None = None
    restore_timer: int = 3000
    _max_letter_length: int = 1

    def __init__(self, master, value: int = 1, **kwargs):
        self._var = ctk.StringVar(value=str(value))
        self._last_valid = value

        vcmd = (master.register(self._on_validate), "%P")
        super().__init__(master, textvariable=self._var,
                         validate="key", validatecommand=vcmd, **kwargs)
        self.bind("<FocusOut>", self._on_focus_out)

    def set_allowed(self, values: set[int] = set()):
        self.allowed = values
        self.check_update_rules()

    def set_value_range(self, value_range: tuple[int | None, int | None] = (None, None)):
        self._value_range = value_range
        self.check_update_rules()

    def _on_validate(self, P: str) -> bool:
        self._cancel_empty_timer()
        if P == "" or P == "-":
            self._schedule_empty_restore()
            return True

        temp_str: list[str] = list(P.strip())
        temp_str_length = len(temp_str)

        if temp_str[0] == "-":
            temp_str_length -= 1

        if self.allowed is not None:
            if temp_str_length > self._max_letter_length:
                self.bell()
                return False
        for i in range(len(temp_str)):
            c = temp_str[i]
            if i == 0 and c == "-":
                continue
            if c not in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}:
                self.bell()
                return False
        num: int = int("".join(temp_str))
        if not self.check_range(num):
            self.bell()
            return False
        self._last_valid = num
        if self.int_var is not None:
            self.int_var.set(num)
        return True

    def check_range(self, i: int) -> bool:
        temp_bool = True
        if self.allowed is not None and len(self.allowed) > 0:
            if i not in self.allowed:
                self.set_int(sorted(self.allowed)[0])
                temp_bool = False
        if self._value_range[0] is not None:
            if i < self._value_range[0]:
                self.set_int(self._value_range[0])
                temp_bool = False
        if self._value_range[1] is not None:
            if i > self._value_range[1]:
                self.set_int(self._value_range[1])
                temp_bool = False
        return temp_bool

    def check_update_rules(self):
        if not self._on_validate(self._var.get()):
            self._restore_last_valid()
            if not self._on_validate(self._var.get()):
                self.check_range(self.get_int())
        self._max_letter_length = 1
        if self.allowed is not None and len(self.allowed) > 0:
            for s in self.allowed:
                self.update_max_letter_length_by_int(s)
        if self._value_range[0] is not None:
            self.update_max_letter_length_by_int(self._value_range[0])
        if self._value_range[1] is not None:
            self.update_max_letter_length_by_int(self._value_range[1])

    def update_max_letter_length_by_int(self, i: int):
        string = i.__str__()
        length = len(string)
        if string[0] == "-":
            length -= 1
        if self._max_letter_length < length:
            self._max_letter_length = length

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
        self._empty_timer = None
        self.configure(validate="none")
        self._var.set(self._last_valid.__str__())
        self.configure(validate="key")
        if self.int_var is not None:
            self.int_var.set(int(self._last_valid))

    def _on_focus_out(self, _e=None):
        if self._var.get() == "":
            self._restore_last_valid()

    def set_int_var(self, value: ctk.IntVar):
        self.int_var = value
        self._on_validate(self._var.get())

    def get_int(self) -> int:
        return self._last_valid

    def set_int(self, v: int):
        self.configure(validate="none")
        self._on_validate(v.__str__())
        self.configure(validate="key")
        self._cancel_empty_timer()