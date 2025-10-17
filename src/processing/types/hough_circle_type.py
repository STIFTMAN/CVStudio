from typing_extensions import TypedDict


class Hough_Circle_Type(TypedDict):
    dp: float
    minDist: int
    param1: int
    param2: int
    minRadius: int
    maxRadius: int
