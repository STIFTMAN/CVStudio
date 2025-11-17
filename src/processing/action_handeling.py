from src.processing.pipeline.canny import canny
from src.processing.feature.hough_circle import hough_circle
from src.processing.feature.hough_rectangle import hough_rectangle
from src.processing.utils.draw_keypoints import draw_keypoints
from src.processing.feature.fast import fast
from src.processing.feature.hough_lines import hough_lines
from src.processing.feature.orb import orb
from src.processing.feature.sift import sift
from src.processing.feature.surf import surf
from src.processing.feature.harris import harris
from src.processing.operations.gamma import gamma
from src.processing.basic_stats_type import Basic_Stats
from src.processing.convolution.ranking import ranking
from src.processing.convolution.default import default
from src.gui.state.project_file_type import Action_Type
from src.processing.operations.linear_contrast_stretch import linear_contrast_stretch
from src.processing.operations.absolute import absolute
from src.processing.operations.clip import clip
from src.processing.operations.negative import negative
from src.processing.operations.clahe import clahe
import numpy
import numpy.typing as npt
import time

feature_mode: list[str] = ["harris", "surf", "sift", "orb", "fast", "hough_lines", "hough_circle", "hough_rectangle"]


def apply_action(image: numpy.ndarray, action: Action_Type, draw_image: numpy.ndarray | None = None) -> tuple[npt.NDArray[numpy.uint8 | numpy.float32], Basic_Stats, npt.NDArray[numpy.uint8] | None]:  # type: ignore
    stats: Basic_Stats = {
        "time": -1,
        "action": action,
        "extended_stats": None,
    }
    start_time = time.time()
    new_img: npt.NDArray[numpy.uint8 | numpy.float32] | None = None
    d_image: npt.NDArray[numpy.uint8] | None = None
    data = action["data"]
    match action['type']:
        case "filter":
            assert not isinstance(data, str)
            if data["settings"]["type"] in ("median", "minimum", "maximum", "25%_quantile", "75%_quantile"):
                kernal = [[1 if y["disabled"] else None for y in x] for x in data["grid"]]
                new_img = ranking(image, kernal, mode=data["settings"]["type"], stride=data["settings"]["spatial_sampling_rate"])  # type: ignore
            elif data["settings"]["type"] == "smoothing":
                kernal = [[y["value"] * data["settings"]["factor"] for y in x] for x in data["grid"]]
                new_img = default(image, kernal, stride=data["settings"]["spatial_sampling_rate"])  # type: ignore
            elif data["settings"]["type"] == "edge_detection":
                kernal = [[y["value"] for y in x] for x in data["grid"]]
                new_img = default(image, kernal, stride=data["settings"]["spatial_sampling_rate"], edge_filter=True)  # type: ignore
        case "operation":
            assert isinstance(data, str)
            match data:
                case "linear_contrast_stretch":
                    new_img = linear_contrast_stretch(image)
                case "absolute":
                    new_img = absolute(image)
                case "clip":
                    new_img = clip(image)
                case "negative":
                    new_img = negative(image)
                case "clahe":
                    new_img = clahe(image)
                case "gamma_025":
                    new_img = gamma(image, 0.25)
                case "gamma_050":
                    new_img = gamma(image, 0.5)
                case "gamma_150":
                    new_img = gamma(image, 1.5)
                case "gamma_200":
                    new_img = gamma(image, 2.0)
                case "gamma_400":
                    new_img = gamma(image, 4.0)
        case "feature":
            assert isinstance(data, str)
            if data in feature_mode:
                match data:
                    case "harris":
                        f_data = harris(image)
                    case "surf":
                        f_data = surf(image)
                    case "sift":
                        f_data = sift(image)
                    case "orb":
                        f_data = orb(image)
                    case "fast":
                        f_data = fast(image)
                    case "hough_lines":
                        f_data = hough_lines(image)
                    case "hough_circle":
                        f_data = hough_circle(image)
                    case "hough_rectangle":
                        f_data = hough_rectangle(image)
                if draw_image is None:
                    if data in ["surf", "hough_lines", "hough_circle", "hough_rectangle"]:
                        d_image = draw_keypoints(image, f_data[1][0], style=f_data[0], scale_with_kp=True)
                    else:
                        d_image = draw_keypoints(image, f_data[1][0], style=f_data[0])
                else:
                    if data in ["surf", "hough_lines", "hough_circle", "hough_rectangle"]:
                        d_image = draw_keypoints(draw_image, f_data[1][0], style=f_data[0], scale_with_kp=True)
                    else:
                        d_image = draw_keypoints(draw_image, f_data[1][0], style=f_data[0])
                stats["extended_stats"] = {
                    "keypoints": f_data[1][0],
                    "descriptors": f_data[1][1]
                }
        case "pipeline":
            assert isinstance(data, str)
            if data == "canny":
                new_img = canny(image)
    stats["time"] = time.time() - start_time
    if new_img is not None:
        return (new_img, stats, None)
    if d_image is not None:
        return (image, stats, d_image)
    return (image, stats, None)
