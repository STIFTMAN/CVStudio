from typing_extensions import TypedDict


class Filter_Settings_Type(TypedDict):
    size: list[int]
    spatial_sampling_rate: list[int]
    factor: float
    type: str
    mutable: bool


class Filter_Cell_Type(TypedDict):
    value: float
    disabled: bool


class Filter_Type(TypedDict):
    settings: Filter_Settings_Type
    grid: list[list[Filter_Cell_Type]]
    name: str


class Project_File_Type(TypedDict):
    filterqueue: list[str]
    image_view_mode: bool


class Action_Type(TypedDict):
    type: str
    data: Filter_Type | str


class Action_Queue_Obj_Type(TypedDict):
    data: Action_Type
    hash: str


empty_project: Project_File_Type = {
    "filterqueue": [],
    "image_view_mode": True
}

empty_filter: Filter_Type = {
    "settings":
    {
        "size": [1, 1],
        "spatial_sampling_rate": [1, 1],
        "factor": 1.0,
        "type": "smoothing",
        "mutable": True
    },
    "grid": [
        [
            {
                "value": 1.0,
                "disabled": False
            }
        ]
    ],
    "name": "my_first_filter"
}
