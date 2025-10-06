import customtkinter as ctk


class DetailsFrame(ctk.CTkFrame):
    """
    Ein einklappbarer Frame (wie <details> im Web).

    Parameter:
        master:            Parent-Widget
        summary:           Text in der Kopfzeile
        open:              bool – startet geöffnet (Default: False)
        padding:           Innenabstand für Inhaltsbereich (tuple[int, int] | int)
        header_padding:    Innenabstand für Kopfzeile (tuple[int, int] | int)
        header_fg_color:   Hintergrundfarbe der Kopfzeile (None = erbt)
        hover:             Hover-Effekt auf der Kopfzeile (Default: True)
        command:           Optionaler Callback, wird nach jedem Toggle aufgerufen (args: is_open: bool)
        **kwargs:          Weitere CTkFrame-Argumente
    """

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

        # Padding-Werte speichern (erst beim Öffnen anwenden!)
        if isinstance(padding, int):
            self._padx = self._pady = padding
        else:
            self._padx, self._pady = padding

        if isinstance(header_padding, int):
            self._hpadx = self._hpady = header_padding
        else:
            self._hpadx, self._hpady = header_padding

        # --- Header (Summary) -------------------------------------------------
        self.header = ctk.CTkButton(
            self,
            fg_color=header_fg_color,
            hover=hover,
            text=self._format_summary_text(summary),
            anchor="w",
            command=self.toggle,           # Klick auf Kopfzeile toggelt
            corner_radius=0,
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=self._hpadx, pady=self._hpady)
        self.grid_columnconfigure(0, weight=1)

        # Tastatur-Accessibility
        self.header.bind("<Return>", lambda e: self.toggle())
        self.header.bind("<space>", lambda e: self.toggle())

        # --- Inhaltscontainer -------------------------------------------------
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid_columnconfigure(0, weight=1)
        # WICHTIG: Hier noch NICHT gridden – Sichtbarkeit steuern wir über open()/close().

        # Startzustand explizit setzen
        if self._is_open:
            self.open()
        else:
            self.close()

    # ========= Public API =====================================================

    @property
    def content(self):
        """Erlaube von außen den Content-Parent zu referenzieren."""
        return self._content

    def add(self, widget, **grid_kwargs):
        """
        Füge ein Kind-Widget in den Inhaltsbereich ein.
        WICHTIG: Das Widget muss mit master=self._content erzeugt worden sein.
        Beispiel:
            child = ctk.CTkLabel(self.content, text="Hallo")
            details.add(child, pady=4, sticky="w")
        """
        # Sicherstellen, dass das Widget den richtigen Parent hat (Reparenting geht in Tkinter nicht)
        if widget.winfo_parent() != str(self._content):
            raise RuntimeError("DetailsFrame.add: widget muss mit master=self._content erzeugt werden.")

        # Auto-Row bestimmen, falls nichts angegeben wurde
        if "row" not in grid_kwargs and "column" not in grid_kwargs:
            next_row = self._content.grid_size()[1]
            grid_kwargs.setdefault("row", next_row)
            grid_kwargs.setdefault("column", 0)
            grid_kwargs.setdefault("sticky", "ew")

        widget.grid(**grid_kwargs)

    def open(self):
        """Inhalt anzeigen."""
        self._is_open = True
        # Erst jetzt Padding anwenden und gridden
        self._content.grid(row=1, column=0, sticky="ew", padx=self._padx, pady=self._pady)
        self._refresh_header()
        if self._command:
            self._command(self._is_open)

    def close(self):
        """Inhalt verbergen."""
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
        """Innenabstand des Inhaltsbereichs setzen. Wirkt live, wenn offen."""
        if isinstance(padding, int):
            self._padx = self._pady = padding
        else:
            self._padx, self._pady = padding
        if self._is_open:
            self._content.grid_configure(padx=self._padx, pady=self._pady)

    def set_header_padding(self, padding):
        """Innenabstand der Kopfzeile setzen (wirkt sofort)."""
        if isinstance(padding, int):
            self._hpadx = self._hpady = padding
        else:
            self._hpadx, self._hpady = padding
        self.header.grid_configure(padx=self._hpadx, pady=self._hpady)

    # ========= Internes =======================================================

    def _format_summary_text(self, summary_text: str) -> str:
        arrow = "▾" if self._is_open else "▸"
        return f"{arrow}  {summary_text}"

    def _refresh_header(self):
        # Pfeil aktualisieren, ursprünglichen Text nach dem Pfeil beibehalten
        current = self.header.cget("text")
        if "  " in current:
            _, text = current.split("  ", 1)
        else:
            text = current
        self.header.configure(text=self._format_summary_text(text))
