import customtkinter as ctk


class FloatEntry(ctk.CTkEntry):
    def __init__(self, master, value: float = 0.0, **kwargs):
        self.var = ctk.StringVar(value=self._format_float(value))
        self._last_good_text = self.var.get()
        vcmd = (master.register(self._on_validate), "%P", "%S")
        super().__init__(master, textvariable=self.var,
                         validate="key", validatecommand=vcmd, **kwargs)
        self.bind("<FocusOut>", self._on_focus_out)

    @staticmethod
    def _format_float(x: float) -> str:
        return f"{float(x):.12g}"

    def _on_validate(self, P: str, S: str) -> bool:
        allowed = set("0123456789-.,")
        if any(ch not in allowed for ch in S):
            self.bell()
            return False

        P = P.strip()

        if P in ("-"):
            return True

        if (P.count("-")) > 1:
            return False
        if "-" in P and not P.startswith("-"):
            return False

        if (P.count(".") + P.count(",")) > 1:
            return False
        try:
            float(P.replace(",", "."))
            self._last_good_text = P
            return True
        except ValueError:
            self.bell()
            return False

    def _on_focus_out(self, _e=None):
        txt = self.var.get().strip()
        if txt in ("-", "."):
            txt = self._last_good_text if self._last_good_text not in ("-", ".") else "0"
        try:
            val = float(txt.replace(",", "."))
            txt = self._format_float(val)
        except ValueError:
            txt = "0"
        if txt != self.var.get():
            self.configure(validate="none")
            self.var.set(txt)
            self.configure(validate="key")

        self._last_good_text = txt

    def get_float(self) -> float:
        self._on_focus_out()
        return float(self.var.get())

    def set_float(self, v: float):
        self.var.set(self._format_float(v))
