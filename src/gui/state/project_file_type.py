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


class Project_File_Type(TypedDict):
    filterqueue: list[Filter_Type | str]
    image_view_mode: bool


template: Project_File_Type = {
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
            ]
        }
    ],
    "image_view_mode": True
}
