from src.processing.convolution.numpy_sequential_ranking import numpy_sequential_ranking
from src.processing.convolution.numpy_sequential import numpy_sequential
from src.gui.state.project_file_type import Action_Type
import numpy
import numpy.typing as npt


def apply_action(image: numpy.ndarray, action: Action_Type) -> tuple[npt.NDArray[numpy.uint8], dict]:  # type: ignore
    match action['type']:
        case "filter":
            f = action["data"]
            assert not isinstance(f, str)
            if f["settings"]["type"] in ("median", "minimum", "maximum", "25%_quantile", "75%_quantile"):
                kernal = [[1 if y["disabled"] else -1 for y in x] for x in f["grid"]]
                new_img = numpy_sequential_ranking(image, kernal, mode=f["settings"]["type"], stride=f["settings"]["spatial_sampling_rate"])  # type: ignore
                # Rangordnungsfilter vorbereitung + anwenden
                return (new_img, {})
            elif f["settings"]["type"] == "smoothing":
                kernal = [[y["value"] * f["settings"]["factor"] for y in x] for x in f["grid"]]
                new_img = numpy_sequential(image, kernal, stride=f["settings"]["spatial_sampling_rate"])  # type: ignore
                return (new_img, {})
            elif f["settings"]["type"] == "edge_detection":
                kernal = [[y["value"] for y in x] for x in f["grid"]]
                new_img = numpy_sequential(image, kernal, stride=f["settings"]["spatial_sampling_rate"])  # type: ignore
                return (new_img, {})
            else:
                return (image, {})
        case "operation":
            return (image, {})
        case "feature":
            return (image, {})
