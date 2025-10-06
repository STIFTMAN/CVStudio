from typing import TypedDict


class Harris_Type(TypedDict):
    maxCorners: int
    qualityLevel: float
    minDistance: int
    blockSize: int
    k: float
