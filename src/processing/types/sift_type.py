from typing_extensions import TypedDict


class Sift_Type(TypedDict):
    nfeatures: int
    nOctaveLayers: int
    contrastThreshold: float
    edgeThreshold: float
    sigma: float
