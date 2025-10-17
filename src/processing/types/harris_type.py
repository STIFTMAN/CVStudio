from typing_extensions import TypedDict


class Harris_Type(TypedDict):
    maxCorners: int
    qualityLevel: float
    minDistance: int
    blockSize: int
    k: float
