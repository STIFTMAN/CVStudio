from typing import TypedDict


class Hough_Lines_Type(TypedDict):
    canny1: int
    canny2: int
    aperture_size: int
    rho: float
    theta_deg: float
    hough_threshold: int
    min_line_length: float
    max_line_gap: float
