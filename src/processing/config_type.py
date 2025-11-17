from typing_extensions import TypedDict

from src.processing.types.canny_type import Canny_Type
from src.processing.types.hough_rectangle_type import Hough_Rectangle_Type
from src.processing.types.hough_circle_type import Hough_Circle_Type
from src.processing.types.hough_lines_type import Hough_Lines_Type
from src.processing.types.fast_type import Fast_Type
from src.processing.types.orb_type import Orb_Type
from src.processing.types.surf_type import Surf_Type
from src.processing.types.harris_type import Harris_Type


class Config_Processing_Feature_Type(TypedDict):
    harris: Harris_Type | None
    surf: Surf_Type | None
    orb: Orb_Type | None
    fast: Fast_Type | None
    hough_lines: Hough_Lines_Type | None
    hough_circle: Hough_Circle_Type | None
    hough_rectangle: Hough_Rectangle_Type | None


class Config_Processing_Pipeline_Type(TypedDict):
    canny: Canny_Type | None


class Config_Processing_Stats_Threshold_Type(TypedDict):
    mean_abs_delta_threshold: float
    std_relative_change_threshold: float
    entropy_bits_delta_threshold: float
    js_divergence_threshold: float
    highfreq_ratio_delta_threshold: float
    colorfulness_delta_threshold: float
    channel_corr_abs_delta_threshold: float
    clipping_fraction_delta_threshold: float


class Config_Processing_Feature_Stats_Threshold_Type(TypedDict):
    kp_rel_drop_threshold: float
    repeatability_abs_drop_threshold: float
    match_precision_abs_drop_threshold: float
    match_recall_abs_drop_threshold: float
    match_inlier_ratio_abs_drop_threshold: float
    kd_repeatability_abs_drop_threshold: float
    kd_kp_rel_drop_threshold: float
    primitive_similarity_abs_drop_threshold: float
    primitive_count_rel_drop_threshold: float


class Config_Processing_Tests_Type(TypedDict):
    angles_deg: list[float]
    scales_f: list[float]
    translations: list[tuple[int, int]]
    ratio: float
    ransac_thresh: float
    repeat_tol_px: float


class Config_Processing_Type(TypedDict):
    feature: Config_Processing_Feature_Type
    pipeline: Config_Processing_Pipeline_Type
    stats_threshold: Config_Processing_Stats_Threshold_Type
    feature_stats_threshold: Config_Processing_Feature_Stats_Threshold_Type
    tests: Config_Processing_Tests_Type
