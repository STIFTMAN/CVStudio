from typing import TypedDict, List


class Harris_Type(TypedDict):
    sigmas: List[float]
    det_thresh: float
    nms_kernel: int
    nms_radius: int
    nms_sigma_factor: float
