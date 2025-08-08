from typing import TypedDict


class Filter_Settings_Type(TypedDict):
    size: list[int]
    spatial_sampling_rate: list[int]
    factor: float
    type: str


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
    name: str
    image_view_mode: bool
    hash: str | None


template: Project_File_Type = {
    "name": "my project",
    "filterqueue": [
        {
            "settings":
            {
                "size": [1, 1],
                "spatial_sampling_rate": [1, 1],
                "factor": 1.0,
                "type": "custom"
            },
            "grid": [
                [
                    {
                        "value": 1.0,
                        "disabled": False
                    }
                ]
            ],
            "name": "my first filter",
            "hash": None
        }
    ],
    "image_view_mode": True,
    "hash": None
}
