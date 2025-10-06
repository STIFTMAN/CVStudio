import customtkinter as ctk


class FlowFrame(ctk.CTkFrame):
    def __init__(self, master=None, hspacing=8, vspacing=8, **kwargs):
        super().__init__(master, **kwargs)
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(fill="both", expand=True, padx=10, pady=10)

        self._items = []
        self._hspacing = hspacing
        self._vspacing = vspacing

        # Reentrancy-/Throttle-Flags
        self._debounce_id = None
        self._is_laying_out = False
        self._last_layout_key = None  # (avail_w, len_items)

        # WICHTIG: auf den *inneren Container* binden, nicht auf self
        self._container.bind("<Configure>", self._on_configure)

    @property
    def container(self):
        return self._container

    def add_label(
        self, text: str, *, border_width: int = 1,
        border_color=None, chip_bg=None, text_color=None, font=None, inner_pad: int = 5, **label_kwargs
    ):
        chip = ctk.CTkFrame(
            self._container,
            border_width=border_width,
            border_color=border_color,
            fg_color=("gray90", "gray20") if chip_bg is None else chip_bg
        )
        lbl = ctk.CTkLabel(chip, text=text, text_color=text_color, font=font, **label_kwargs)
        lbl.pack(padx=inner_pad * 2, pady=inner_pad)

        self._items.append(chip)
        self._relayout(force=True)  # explizit neu anordnen, wenn Inhalte sich ändern
        return lbl

    def clear(self):
        for w in self._items:
            try:
                w.grid_forget()
                w.destroy()
            except Exception:
                pass
        self._items.clear()
        self._relayout(force=True)

    # ----- Events / Debounce -----
    def _on_configure(self, _):
        # Wenn gerade gelayoutet wird, kein neues Debounce aufbauen
        if self._is_laying_out:
            return
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(40, self._relayout)

    # ----- Layout -----
    def _relayout(self, force: bool = False):
        # Debounce-Timer „verbrauchen“
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
            self._debounce_id = None

        if self._is_laying_out:
            return  # zusätzlicher Schutz

        avail_w = self._container.winfo_width()
        if avail_w <= 1:
            # Einmalig später versuchen; kein Dauerschleifen, weil kein Configure gebunden ist
            self.after(20, lambda: self._relayout(force))
            return

        # Nur neu layouten, wenn sich Breite oder Item-Anzahl geändert hat oder force=True
        layout_key = (avail_w, len(self._items))
        if not force and layout_key == self._last_layout_key:
            return

        self._is_laying_out = True
        try:
            # alte Grid-Positionen löschen
            for w in self._items:
                try:
                    w.grid_forget()
                except Exception:
                    pass

            x = 0
            row = 0
            col = 0
            for chip in self._items:
                # Keine update_idletasks(): vermeidet neue Configure-Events
                req_w = chip.winfo_reqwidth()

                # Linkes Außenpadding (nur zwischen Chips)
                left_pad = 0 if col == 0 else self._hspacing

                # Zeilenumbruch?
                if col != 0 and (x + left_pad + req_w) > avail_w:
                    row += 1
                    col = 0
                    x = 0
                    left_pad = 0

                chip.grid(
                    row=row, column=col,
                    padx=(left_pad, 0),
                    pady=(self._vspacing if row > 0 else 0),
                    sticky="w"
                )

                x += left_pad + req_w
                col += 1

            # keine Streckung
            for i in range(col + 1):
                self._container.grid_columnconfigure(i, weight=0)

            self._last_layout_key = layout_key
        finally:
            self._is_laying_out = False
