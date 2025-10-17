from typing import Any
from typing_extensions import TypedDict
from src.gui.state.project_file_type import Action_Type


class Basic_Stats(TypedDict):
    time: float
    action: Action_Type
    extended_stats: dict[str, Any] | None
