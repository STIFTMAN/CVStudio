from typing_extensions import TypedDict


class Surf_Type(TypedDict):
    hessianThreshold: float
    nOctaves: int
    nOctaveLayers: int
    extended: bool
    upright: bool
