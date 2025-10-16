import threading
from typing import Any
from src.gui.utils.format_nested import format_nested
from src.gui.components.details_frame import DetailsFrame
from src.gui.utils.config_loader import get_setting
import customtkinter
import src.gui.state.root as root


class TestWindow(customtkinter.CTkToplevel):

    action_frame: customtkinter.CTkFrame | None = None
    container: customtkinter.CTkScrollableFrame | None = None
    progressbar: customtkinter.CTkProgressBar | None = None

    def __init__(self, master, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.title(get_setting("name"))
        self.after(250, lambda: self.iconbitmap("src/assets/favicon.ico"))

        test_window_size = get_setting("window_size")["test"]
        screen_coords = (
            int((master.winfo_screenwidth() - test_window_size[0]) / 2),
            int((master.winfo_screenheight() - test_window_size[1]) / 2),
        )
        self.geometry(
            f"{test_window_size[0]}x{test_window_size[1]}+{screen_coords[0]}+{screen_coords[1]}"
        )
        self.after(100, self.focus)

        self.build_buttons_frame()
        self.build_container()
        self.build_results()

    # ----------------------------- Layout Container -----------------------------

    def build_container(self):
        """Hauptbereich: Scrollbarer Stack für Sektionen."""
        self.clear_container()
        if self.container is None:
            self.container = customtkinter.CTkScrollableFrame(master=self)
            # Außenfläche füllt das Fenster, damit intern gescrollt werden kann
            self.container.pack(fill="both", expand=True, padx=8, pady=8)

    def clear_container(self):
        if self.container is not None and self.container.winfo_exists():
            for child in self.container.winfo_children():
                child.destroy()

    # ----------------------------- Header / Actions -----------------------------

    def build_buttons_frame(self):
        self.action_frame = customtkinter.CTkFrame(master=self)
        # Header nur horizontal füllen
        self.action_frame.pack(fill="x", padx=8, pady=(8, 0), anchor="n")

        status_label: customtkinter.CTkLabel = customtkinter.CTkLabel(
            master=self.action_frame, textvariable=root.status_test, anchor="w"
        )
        self.progressbar = customtkinter.CTkProgressBar(
            master=self.action_frame, variable=root.current_project.progress_test
        )
        button_quicktest: customtkinter.CTkButton = customtkinter.CTkButton(
            master=self.action_frame, text="QuickTest", command=self.run_quicktest
        )

        # In einer Row von links nach rechts
        status_label.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        self.progressbar.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        button_quicktest.pack(side="left", padx=5, pady=8)

    # ----------------------------- Aktionen -----------------------------

    def run_quicktest(self):
        assert root.status_test is not None
        if not root.current_project.image_ready():
            root.status_test.set("NO IMAGE")
            return

        def runner():
            assert root.status_test is not None and root.current_project.progress_test is not None
            root.status_test.set("START TEST")
            root.current_project.progress_test.set(0.0)
            root.current_project.quick_test()
            root.status_test.set("END TEST")
            root.current_project.progress_test.set(1.0)
            # UI-Update im Hauptthread planen
            self.after(0, self.build_results)

        threading.Thread(target=runner, daemon=True).start()

    def run_fulltest(self):
        pass

    # ----------------------------- Ergebnisse rendern -----------------------------

    def build_results(self):
        if root.current_project.test_results is None:
            return

        self.clear_container()

        # Oberer Stack-Container für ALLE Sektionen (ein Parent = konsistent)
        assessment_frame: customtkinter.CTkFrame = customtkinter.CTkFrame(
            master=self.container
        )
        # WICHTIG: in vertikalen Listen außen KEIN expand, NUR fill="x"
        assessment_frame.pack(fill="x", expand=False, padx=8, pady=6, anchor="n")

        # --- Basic ---
        basic_stats_summary = self.build_custom_container(
            assessment_frame,
            "Basic Stats Summary",
            root.current_project.test_results["basic"]["extended_stats"]["assessment"][
                "summary"
            ],
        )
        basic_stats_summary.pack(fill="x", expand=False, padx=8, pady=6, anchor="n")

        basic_stats_notes = self.build_custom_container(
            assessment_frame,
            "Basic Stats Notes",
            root.current_project.test_results["basic"]["extended_stats"]["assessment"][
                "notes"
            ],
        )
        basic_stats_notes.pack(fill="x", expand=False, padx=8, pady=6, anchor="n")

        # --- Optional Feature ---
        if root.current_project.test_results["feature"] is not None:
            feature_stats_summary = self.build_custom_container(
                assessment_frame,
                "Feature Stats Summary",
                root.current_project.test_results["feature"]["assessment"]["summary"],
            )
            feature_stats_summary.pack(fill="x", expand=False, padx=8, pady=6, anchor="n")

            feature_stats_notes = self.build_custom_container(
                assessment_frame,
                "Feature Stats Notes",
                root.current_project.test_results["feature"]["assessment"]["notes"],
            )
            feature_stats_notes.pack(fill="x", expand=False, padx=8, pady=6, anchor="n")

            details_basic_stats: DetailsFrame = self.build_details_basic_stats(
                assessment_frame
            )
            details_basic_stats.pack(
                fill="x", expand=False, padx=8, pady=6, anchor="n"
            )

            details_feature_stats: DetailsFrame = self.build_details_feature_stats(
                assessment_frame
            )
            details_feature_stats.pack(
                fill="x", expand=False, padx=8, pady=6, anchor="n"
            )
        else:
            details_basic_stats: DetailsFrame = self.build_details_basic_stats(
                assessment_frame
            )
            details_basic_stats.pack(
                fill="x", expand=False, padx=8, pady=6, anchor="n"
            )

    # ----------------------------- Details-Bereiche -----------------------------

    def build_details_basic_stats(self, parent) -> DetailsFrame:
        # Rot, geöffnet; Parent ist der gleiche Stack wie oben
        details_basic_stats: DetailsFrame = DetailsFrame(
            master=parent, summary="details_basic_stats", open=False
        )

        assert (
            root.current_project is not None
            and root.current_project.test_results is not None
        )
        data: list[tuple[str, Any | None]] = [
            ("time overall", root.current_project.test_results["basic"]["time"]),
            (
                "thresholds_used",
                root.current_project.test_results["basic"]["extended_stats"][
                    "thresholds_used"
                ],
            ),
            (
                "meta",
                root.current_project.test_results["basic"]["extended_stats"]["meta"],
            ),
            (
                "diff",
                root.current_project.test_results["basic"]["extended_stats"]["diff"],
            ),
            (
                "flags",
                root.current_project.test_results["basic"]["extended_stats"]["flags"],
            ),
            (
                "data before",
                root.current_project.test_results["basic"]["extended_stats"]["raw"]["before"],
            ),
            (
                "data after",
                root.current_project.test_results["basic"]["extended_stats"]["raw"]["after"],
            ),
        ]
        for title, payload in data:
            child = self.build_custom_container(details_basic_stats._content, title, payload)
            details_basic_stats.add(child, padx=[10, 10], pady=[10, 10])
            # (Wenn dein add() NICHT packt, ersetze die Zeile oben durch:)
            # child.pack(fill="x", expand=False, padx=8, pady=6, anchor="n")
        details_basic_stats.after(20, details_basic_stats.close)
        return details_basic_stats

    def build_details_feature_stats(self, parent) -> DetailsFrame:
        details_feature_stats: DetailsFrame = DetailsFrame(
            master=parent, summary="details_feature_stats", open=False
        )
        assert (
            root.current_project is not None
            and root.current_project.test_results is not None
        )
        data: list[tuple[str, Any | None]] = [
            ("thresholds_used", root.current_project.test_results["feature"]["thresholds_used"]),
            ("diff", root.current_project.test_results["feature"]["diff"]),
            ("flags", root.current_project.test_results["feature"]["flags"]),
            ("data_before", root.current_project.test_results["feature"]["raw"]["before"]),
            ("data_after", root.current_project.test_results["feature"]["raw"]["after"])
        ]
        for title, payload in data:
            child = self.build_custom_container(details_feature_stats._content, title, payload)
            details_feature_stats.add(child, padx=[10, 10], pady=[10, 10])
        details_feature_stats.after(20, details_feature_stats.close)
        return details_feature_stats

    # ----------------------------- Baustein: Card mit Titel + Text -----------------------------

    def build_custom_container(self, master, title: str, data: Any) -> customtkinter.CTkFrame:
        """
        Eine kompakte Card:
        - Titel linksbündig
        - darunter Textbox (feste Höhe), Wortumbruch, read-only
        - außen KEIN expand (damit Cards ihre natürliche Höhe behalten)
        """
        custom_container: customtkinter.CTkFrame = customtkinter.CTkFrame(master=master)

        titel_label: customtkinter.CTkLabel = customtkinter.CTkLabel(
            master=custom_container, text=title, anchor="w", justify="left"
        )
        titel_label.pack(fill="x", padx=10, pady=(10, 0))

        string: str = format_nested(data)

        line_height: int = min(len(string.splitlines()) * 15 + 50, 500)

        textbox = customtkinter.CTkTextbox(master=custom_container, height=line_height, activate_scrollbars=True)
        textbox.insert("1.0", string)
        textbox.configure(state="disabled", wrap="word")
        textbox.pack(fill="x", padx=10, pady=10)

        return custom_container
