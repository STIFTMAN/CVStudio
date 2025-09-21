from src.processing.operations.gamma import gamma
from src.processing.stats_type import Stats
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


def apply_action(image: numpy.ndarray, action: Action_Type) -> tuple[npt.NDArray[numpy.uint8 | numpy.float32], Stats]:  # type: ignore
    stats: Stats = {
        "time": -1,
        "action": action,
        "extended_stats": None,
    }
    start_time = time.time()
    match action['type']:
        case "filter":
            f = action["data"]
            assert not isinstance(f, str)
            if f["settings"]["type"] in ("median", "minimum", "maximum", "25%_quantile", "75%_quantile"):
                kernal = [[1 if y["disabled"] else None for y in x] for x in f["grid"]]
                new_img = ranking(image, kernal, mode=f["settings"]["type"], stride=f["settings"]["spatial_sampling_rate"])  # type: ignore
                stats["time"] = time.time() - start_time
                return (new_img, stats)
            elif f["settings"]["type"] == "smoothing":
                kernal = [[y["value"] * f["settings"]["factor"] for y in x] for x in f["grid"]]
                new_img = default(image, kernal, stride=f["settings"]["spatial_sampling_rate"])  # type: ignore
                return (new_img, stats)
            elif f["settings"]["type"] == "edge_detection":
                kernal = [[y["value"] for y in x] for x in f["grid"]]
                new_img = default(image, kernal, stride=f["settings"]["spatial_sampling_rate"], edge_filter=True)  # type: ignore
                stats["time"] = time.time() - start_time
                return (new_img, stats)
            else:
                return (image, stats)
        case "operation":
            o = action["data"]
            assert isinstance(o, str)
            new_img: npt.NDArray[numpy.uint8 | numpy.float32] | None = None
            match o:
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
                case "gamma_100":
                    new_img = gamma(image, 1.0)
                case "gamma_200":
                    new_img = gamma(image, 2.0)
                case "gamma_400":
                    new_img = gamma(image, 4.0)
            stats["time"] = time.time() - start_time
            if new_img is not None:
                return (new_img, stats)
            return (image, stats)
        case "feature":
            stats["time"] = time.time() - start_time
            return (image, stats)
