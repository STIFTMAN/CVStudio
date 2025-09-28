from typing import TypedDict

from src.processing.types.hough_type import Hough_Type
from src.processing.types.fast_type import Fast_Type
from src.processing.types.orb_type import Orb_Type
from src.processing.types.surf_type import Surf_Type
from src.processing.types.harris_type import Harris_Type


class Config_Processing_Type(TypedDict):
    harris: Harris_Type | None
    surf: Surf_Type | None
    orb: Orb_Type | None
    fast: Fast_Type | None
    hough: Hough_Type | None
