from typing import TypedDict


class Orb_Type(TypedDict):
    nfeatures: int
    scaleFactor: float
    nlevels: int
    edgeThreshold: int
    firstLevel: int
    WTA_K: int
    scoreType: int
    patchSize: int
    fastThreshold: int
