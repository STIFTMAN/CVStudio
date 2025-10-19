from typing import Literal
from datetime import datetime
import sys
import customtkinter
from src.gui.utils.open_app import open_app

_MODE = Literal["init_reset", "continue"]
TEXT_TYPE = Literal["ERROR", "INFO", "WARNING", "CRITICAL ERROR"]


class Logger():
    _path: str = "."
    _log_name: str = "log.txt"
    _print_date: bool = True
    _print_tag: bool = True
    _open_log_on_critical_error: bool = True
    _notifier: customtkinter.BooleanVar | None = None
    _print_console: bool = True

    def __init__(self, mode: _MODE = "continue"):
        if mode == "init_reset":
            self.reset()

    def set_notifier(self, notifier: customtkinter.BooleanVar | None = None):
        self._notifier = notifier

    def read_notifier(self):
        if self._notifier is not None:
            self._notifier.set(False)

    def reset(self):
        if self._print_console:
            print("---RESET---")
        open(f"{self._path}/{self._log_name}", "w", encoding="utf-8").close()

    def write(self, text: str = "", tag: TEXT_TYPE | None = None, modulename: str = "", end="\n"):
        line = ""
        if self._print_date:
            line += f'[{datetime.now().strftime("%H:%M:%S")}]'
        if self._print_tag:
            line += f'[{tag}]'
        if len(modulename) > 0:
            line += f'[{modulename}]'
        line += f' {text}{end}'
        with open(f"{self._path}/{self._log_name}", "a+", encoding="utf-8") as f:
            if self._print_console:
                print(line)
            f.write(line)
        if tag == "CRITICAL ERROR":
            if self._open_log_on_critical_error:
                open_app(f"{self._path}/{self._log_name}")
                if self._print_console:
                    print("---TERMINATE APPLICATION---")
            sys.exit(1)
        if self._notifier is not None:
            self._notifier.set(True)


log: Logger = Logger()
