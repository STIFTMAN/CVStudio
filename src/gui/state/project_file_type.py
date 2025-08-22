from typing import TypedDict


class Filter_Settings_Type(TypedDict):
    size: list[int]
    spatial_sampling_rate: list[int]
    factor: float
    type: str
    mutable: bool
    args: int


class Filter_Cell_Type(TypedDict):
    value: float
    disabled: bool


class Filter_Type(TypedDict):
    settings: Filter_Settings_Type
    grid: list[list[Filter_Cell_Type]]
    name: str
    hash: str | None


class Project_File_Type(TypedDict):
    filterqueue: list[Filter_Type | str]
    image_view_mode: bool
    hash: str | None


empty_project: Project_File_Type = {
    "filterqueue": [],
    "image_view_mode": True,
    "hash": None
}

empty_filter: Filter_Type = {
    "settings":
    {
        "size": [1, 1],
        "spatial_sampling_rate": [1, 1],
        "factor": 1.0,
        "type": "custom",
        "mutable": True,
        "args": 0
    },
    "grid": [
        [
            {
                "value": 1.0,
                "disabled": False
            }
        ]
    ],
    "name": "my_first_filter",
    "hash": None
}
