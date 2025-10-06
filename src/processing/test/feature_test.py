from __future__ import annotations
from typing import Dict, Any, List, Callable, Tuple, Iterable
import numpy as np

from src.processing.test.metrics import affine_to_points, orb_match_metrics, repeatability, sift_match_metrics
from src.processing.utils.transform_keypoints import (
    keypoint_circle_to_C3, keypoint_line_to_L4, keypoint_rect_to_R5, keypoint_to_xy
)
from src.processing.test.similarity import circle_similarity, line_similarity, rect_similarity

from src.processing.feature.fast import fast
from src.processing.feature.harris import harris
from src.processing.feature.orb import orb
from src.processing.feature.sift import sift
from src.processing.feature.surf import surf

from src.processing.feature.hough_lines import hough_lines
from src.processing.feature.hough_circle import hough_circle
from src.processing.feature.hough_rectangle import hough_rectangle

from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.utils.warps import rotate, scale, translate


# =========================
# global config (edit here)
# =========================
GLOBAL_TEST_CONFIG: Dict[str, Any] = {
    # multiple transforms to evaluate (each compared against the base image)
    "angles_deg": [10.0, 30.0, 45.0, 60.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0],            # list[float]
    "scales_f": [0.1, 0.25, 0.5, 0.75, 1.33, 2.0, 4.0, 10.0],              # list[float]
    "translations": [(1, 0), (0, 1), (1, 1), (5, 5), (20, 20), (50, 50), (100, 100), (200, 200)],  # list[tuple[tx, ty]]

    # matching / metrics constants
    "ratio": 0.75,
    "ransac_thresh": 3.0,
    "repeat_tol_px": 3.0,
}

_VALID_FEATURES = {
    "harris", "fast",                 # detectors_only
    "sift", "surf", "orb",            # keypoint_descriptor
    "hough_lines", "hough_circle", "hough_rectangle",  # geometric_primitives
}


def _accumulate_transforms(
    base_img: np.ndarray,
    names: Iterable[Tuple[str, Any]],
    warp_fn: Callable[[np.ndarray, Any], Tuple[np.ndarray, np.ndarray]],
    eval_fn: Callable[[np.ndarray, np.ndarray, str], Dict[str, Any]],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for label, param in names:
        img_w, M = warp_fn(base_img, param)
        out[str(label)] = eval_fn(img_w, M, str(label))
    return out


def run_selected_feature_tests(
    image: np.ndarray,
    feature_mode: List[str],
) -> Dict[str, Any]:
    """
    Run tests only for the requested features.
    feature_mode ⊆ ["harris","surf","sift","orb","fast","hough_lines","hough_circle","hough_rectangle"].
    Uses only GLOBAL_TEST_CONFIG (no overrides).
    """
    # validate features
    req = [f.lower() for f in feature_mode]
    unknown = [f for f in req if f not in _VALID_FEATURES]
    if unknown:
        raise ValueError(f"Unknown feature(s): {unknown}. Allowed: {sorted(_VALID_FEATURES)}")

    cfg = GLOBAL_TEST_CONFIG  # use globals only
    base = to_gray_uint8(image)

    results: Dict[str, Any] = {}

    # which groups to evaluate
    do_det = any(f in req for f in ("harris", "fast"))
    do_kd = any(f in req for f in ("sift", "surf", "orb"))
    do_geo = any(f in req for f in ("hough_lines", "hough_circle", "hough_rectangle"))

    # ---------------------------------
    # DETECTORS ONLY (repeatability)
    # ---------------------------------
    if do_det:
        def _eval_detectors(img_w: np.ndarray, M: np.ndarray, _label: str) -> Dict[str, Any]:
            block: Dict[str, Any] = {}
            if "harris" in req:
                kA, _ = harris(base)[1]
                kW, _ = harris(img_w)[1]
                rep = repeatability(affine_to_points(keypoint_to_xy(kA), M),
                                    keypoint_to_xy(kW),
                                    tol_px=float(cfg["repeat_tol_px"]))
                block["harris"] = {"base": {"num_kp": len(kA)},
                                   "warped": {"num_kp": len(kW), "repeatability": rep}}
            if "fast" in req:
                kA, _ = fast(base)[1]
                kW, _ = fast(img_w)[1]
                rep = repeatability(affine_to_points(keypoint_to_xy(kA), M),
                                    keypoint_to_xy(kW),
                                    tol_px=float(cfg["repeat_tol_px"]))
                block["fast"] = {"base": {"num_kp": len(kA)},
                                 "warped": {"num_kp": len(kW), "repeatability": rep}}
            return block

        det_results: Dict[str, Any] = {}
        det_results.update(_accumulate_transforms(base, [(f"rot_{a}", a) for a in cfg.get("angles_deg", [])], rotate, _eval_detectors))
        det_results.update(_accumulate_transforms(base, [(f"scl_{s}", s) for s in cfg.get("scales_f", [])], scale, _eval_detectors))
        det_results.update(_accumulate_transforms(base, [(f"trn_{tx}_{ty}", (tx, ty)) for (tx, ty) in cfg.get("translations", [])],
                                                  lambda img, t: translate(img, t[0], t[1]), _eval_detectors))
        results["detectors_only"] = det_results

    # ---------------------------------
    # KEYPOINT + DESCRIPTOR
    # ---------------------------------
    if do_kd:
        def _eval_kd(img_w: np.ndarray, M: np.ndarray, _label: str) -> Dict[str, Any]:
            block: Dict[str, Any] = {}

            def _run(detcompute, name: str):
                kpA, desA = detcompute(base)[1]
                kpW, desW = detcompute(img_w)[1]
                desA = desA if desA is not None else np.empty((0, 128), np.float32)
                desW = desW if desW is not None else np.empty_like(desA)

                if desA.dtype == np.uint8:
                    metr = orb_match_metrics(desA, desW, kpA, kpW, float(cfg["ratio"]), float(cfg["ransac_thresh"]))
                else:
                    metr = sift_match_metrics(desA, desW, kpA, kpW, float(cfg["ratio"]), float(cfg["ransac_thresh"]))

                rep = repeatability(affine_to_points(keypoint_to_xy(kpA), M),
                                    keypoint_to_xy(kpW),
                                    tol_px=float(cfg["repeat_tol_px"]))
                block[name] = {"base": {"num_kp": len(kpA)},
                               "warped": {"num_kp": len(kpW), **metr, "repeatability": rep}}

            if "sift" in req:
                _run(sift, "sift")
            if "surf" in req:
                _run(surf, "surf")
            if "orb" in req:
                _run(orb, "orb")
            return block

        kd_results: Dict[str, Any] = {}
        kd_results.update(_accumulate_transforms(base, [(f"rot_{a}", a) for a in cfg.get("angles_deg", [])], rotate, _eval_kd))
        kd_results.update(_accumulate_transforms(base, [(f"scl_{s}", s) for s in cfg.get("scales_f", [])], scale, _eval_kd))
        kd_results.update(_accumulate_transforms(base, [(f"trn_{tx}_{ty}", (tx, ty)) for (tx, ty) in cfg.get("translations", [])],
                                                 lambda img, t: translate(img, t[0], t[1]), _eval_kd))
        results["keypoint_descriptor"] = kd_results

    # ---------------------------------
    # GEOMETRIC PRIMITIVES
    # ---------------------------------
    if do_geo:
        geo: Dict[str, Any] = {}

        # detect once on base
        base_lines = base_circles = base_rects = None
        if "hough_lines" in req:
            k_base, _ = hough_lines(base)[1]
            base_lines = keypoint_line_to_L4(k_base)
            geo["line"] = {}
        if "hough_circle" in req:
            k_base, _ = hough_circle(base)[1]
            base_circles = keypoint_circle_to_C3(k_base)
            geo["circle"] = {}
        if "hough_rectangle" in req:
            k_base, _ = hough_rectangle(base)[1]
            base_rects = keypoint_rect_to_R5(k_base)
            geo["rect"] = {}

        def _eval_geo(img_w: np.ndarray, _M: np.ndarray, kind: str) -> Dict[str, Any]:
            if kind == "line" and base_lines is not None:
                kW, _ = hough_lines(img_w)[1]
                L_W = keypoint_line_to_L4(kW)
                return {"num": int(L_W.shape[0]), "similarity": line_similarity(base_lines, L_W)}
            if kind == "circle" and base_circles is not None:
                kW, _ = hough_circle(img_w)[1]
                C_W = keypoint_circle_to_C3(kW)
                return {"num": int(C_W.shape[0]), "similarity": circle_similarity(base_circles, C_W)}
            if kind == "rect" and base_rects is not None:
                kW, _ = hough_rectangle(img_w)[1]
                R_W = keypoint_rect_to_R5(kW)
                return {"num": int(R_W.shape[0]), "similarity": rect_similarity(base_rects, R_W)}
            return {}

        def _accum(kind: str, pairs: Iterable[Tuple[str, Any]], warp):
            if kind not in geo:
                return
            for label, param in pairs:
                img_w, M = warp(base, param)
                geo[kind][str(label)] = _eval_geo(img_w, M, kind)

        _accum("line", [(f"rot_{a}", a) for a in cfg.get("angles_deg", [])], rotate)
        _accum("line", [(f"scl_{s}", s) for s in cfg.get("scales_f", [])], scale)
        _accum("line", [(f"trn_{tx}_{ty}", (tx, ty)) for (tx, ty) in cfg.get("translations", [])], lambda img, t: translate(img, t[0], t[1]))
        _accum("circle", [(f"rot_{a}", a) for a in cfg.get("angles_deg", [])], rotate)
        _accum("circle", [(f"scl_{s}", s) for s in cfg.get("scales_f", [])], scale)
        _accum("circle", [(f"trn_{tx}_{ty}", (tx, ty)) for (tx, ty) in cfg.get("translations", [])], lambda img, t: translate(img, t[0], t[1]))
        _accum("rect", [(f"rot_{a}", a) for a in cfg.get("angles_deg", [])], rotate)
        _accum("rect", [(f"scl_{s}", s) for s in cfg.get("scales_f", [])], scale)
        _accum("rect", [(f"trn_{tx}_{ty}", (tx, ty)) for (tx, ty) in cfg.get("translations", [])], lambda img, t: translate(img, t[0], t[1]))

        results["geometric_primitives"] = geo

    return results
