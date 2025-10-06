from __future__ import annotations
from typing import Dict, Any, Optional, List
import numpy as np
import src.gui.state.root as root

# --------------------------------------------
# Zentrale Schwellwerte (wie zuvor)
# --------------------------------------------
FEATURE_ALERT_THRESHOLDS: Dict[str, float] = {
    # Detektoren (Harris/FAST)
    "kp_rel_drop_threshold": 0.35,
    "repeatability_abs_drop_threshold": 0.10,

    # Keypoint+Descriptor (SIFT/SURF/ORB)
    "match_precision_abs_drop_threshold": 0.10,
    "match_recall_abs_drop_threshold": 0.10,
    "match_inlier_ratio_abs_drop_threshold": 0.10,
    "kd_repeatability_abs_drop_threshold": 0.10,
    "kd_kp_rel_drop_threshold": 0.35,

    # Geometrische Primitive (Hough)
    "primitive_similarity_abs_drop_threshold": 0.10,
    "primitive_count_rel_drop_threshold": 0.35,
}


def _safe_get(d: Dict[str, Any], path: List[str], default=None):
    node = d
    for k in path:
        if not (isinstance(node, dict) and k in node):
            return default
        node = node[k]
    return node


def _safe_num(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    except Exception:
        return None


def _delta(a: Optional[float], b: Optional[float]) -> Optional[float]:
    return None if (a is None or b is None) else float(b - a)


def _rel_drop(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    if a == 0:
        return None
    return float((a - b) / abs(a))


def analyze_feature_tests_delta_from_results(
    before_res: Dict[str, Any],
    after_res: Dict[str, Any],
) -> Dict[str, Any]:
    th = FEATURE_ALERT_THRESHOLDS

    flags: List[str] = []
    notes: List[str] = []

    diff: Dict[str, Any] = {
        "detectors_only": {},
        "keypoint_descriptor": {},
        "geometric_primitives": {}
    }

    # =====================================================
    # 1) DETECTORS ONLY (Harris, FAST)
    # =====================================================
    det_before = before_res.get("detectors_only") or {}
    det_after = after_res.get("detectors_only") or {}

    det_diff: Dict[str, Any] = {}
    for transform_label, block_before in det_before.items():
        block_after = det_after.get(transform_label, {})
        features = set(block_before.keys()) | set(block_after.keys())
        t_entry: Dict[str, Any] = {}
        for feat in sorted(features):
            b = block_before.get(feat, {})
            a = block_after.get(feat, {})

            kp_b = _safe_num(_safe_get(b, ["base", "num_kp"]))
            kp_a = _safe_num(_safe_get(a, ["base", "num_kp"]))
            rep_b = _safe_num(_safe_get(b, ["warped", "repeatability"]))
            rep_a = _safe_num(_safe_get(a, ["warped", "repeatability"]))

            kp_rel_drop = _rel_drop(kp_b, kp_a)
            rep_delta = _delta(rep_b, rep_a)

            t_entry[feat] = {
                "num_kp_before": kp_b,
                "num_kp_after": kp_a,
                "num_kp_rel_drop": kp_rel_drop,  # positiv = Rückgang
                "repeatability_before": rep_b,
                "repeatability_after": rep_a,
                "repeatability_delta": rep_delta
            }

            if kp_rel_drop is not None and kp_rel_drop > th["kp_rel_drop_threshold"]:
                flags.append("detectors_keypoints_drop")
                notes.append(f"{root.current_lang.get('analysis_notes_keypoints_drop').get()} "
                             f"{feat}@{transform_label}: −{kp_rel_drop*100:.1f}%")

            if rep_delta is not None and rep_delta < -th["repeatability_abs_drop_threshold"]:
                flags.append("detectors_repeatability_drop")
                # Prozent statt Absolutwert:
                notes.append(f"{root.current_lang.get('analysis_notes_repeatability_drop').get()} "
                             f"{feat}@{transform_label}: {rep_delta*100:+.1f}%")

        det_diff[transform_label] = t_entry

    if det_diff:
        diff["detectors_only"] = det_diff

    # =====================================================
    # 2) KEYPOINT + DESCRIPTOR (SIFT/SURF/ORB)
    # =====================================================
    kd_before = before_res.get("keypoint_descriptor") or {}
    kd_after = after_res.get("keypoint_descriptor") or {}

    kd_diff: Dict[str, Any] = {}
    KNOWN_THRESHOLDS_BY_KEY = {
        "precision": "match_precision_abs_drop_threshold",
        "recall": "match_recall_abs_drop_threshold",
        "inlier_ratio": "match_inlier_ratio_abs_drop_threshold",
        "repeatability": "kd_repeatability_abs_drop_threshold",
    }

    for transform_label, block_before in kd_before.items():
        block_after = kd_after.get(transform_label, {})
        t_entry: Dict[str, Any] = {}
        features = set(block_before.keys()) | set(block_after.keys())
        for feat in sorted(features):
            b = block_before.get(feat, {})
            a = block_after.get(feat, {})

            kp_b = _safe_num(_safe_get(b, ["base", "num_kp"]))
            kp_a = _safe_num(_safe_get(a, ["base", "num_kp"]))
            kp_rel_drop = _rel_drop(kp_b, kp_a)

            warped_b = _safe_get(b, ["warped"], {}) or {}
            warped_a = _safe_get(a, ["warped"], {}) or {}

            metric_keys = set()
            for k, v in warped_b.items():
                if _safe_num(v) is not None:
                    metric_keys.add(k)
            for k, v in warped_a.items():
                if _safe_num(v) is not None:
                    metric_keys.add(k)

            metr_deltas: Dict[str, Any] = {}
            for mk in sorted(metric_keys):
                vb = _safe_num(warped_b.get(mk))
                va = _safe_num(warped_a.get(mk))
                delta = _delta(vb, va)
                metr_deltas[mk] = {"before": vb, "after": va, "delta": delta}

                thr_key = KNOWN_THRESHOLDS_BY_KEY.get(mk)
                if thr_key and vb is not None and va is not None:
                    if (va - vb) < -th[thr_key]:
                        if mk == "repeatability":
                            flags.append("kd_repeatability_drop")
                            # Prozent statt Absolutwert:
                            notes.append(f"{root.current_lang.get('analysis_notes_repeatability_drop').get()} "
                                         f"{feat}@{transform_label}: {delta * 100:+.1f}%")  # type: ignore
                        else:
                            flags.append(f"kd_{mk}_drop")
                            # Prozent statt Absolutwert:
                            notes.append(f"{root.current_lang.get('analysis_notes_matching_quality_drop').get()} "
                                         f"{feat}@{transform_label} ({mk} {delta * 100:+.1f}%)")  # type: ignore

            if kp_rel_drop is not None and kp_rel_drop > th["kd_kp_rel_drop_threshold"]:
                flags.append("kd_keypoints_drop")
                notes.append(f"{root.current_lang.get('analysis_notes_keypoints_drop').get()} "
                             f"{feat}@{transform_label}: −{kp_rel_drop*100:.1f}%")

            t_entry[feat] = {
                "num_kp_before": kp_b,
                "num_kp_after": kp_a,
                "num_kp_rel_drop": kp_rel_drop,
                "metrics": metr_deltas
            }

        kd_diff[transform_label] = t_entry

    if kd_diff:
        diff["keypoint_descriptor"] = kd_diff

    # =====================================================
    # 3) GEOMETRISCHE PRIMITIVE (Line/Circle/Rect)
    # =====================================================
    geo_before = before_res.get("geometric_primitives") or {}
    geo_after = after_res.get("geometric_primitives") or {}

    geo_diff: Dict[str, Any] = {}
    for kind in ("line", "circle", "rect"):
        kb = geo_before.get(kind) or {}
        ka = geo_after.get(kind) or {}
        if not (kb or ka):
            continue
        kind_entry: Dict[str, Any] = {}
        transforms = set(kb.keys()) | set(ka.keys())
        for transform_label in sorted(transforms):
            b = kb.get(transform_label, {})
            a = ka.get(transform_label, {})
            num_b = _safe_num(b.get("num"))
            num_a = _safe_num(a.get("num"))
            sim_b = _safe_num(b.get("similarity"))
            sim_a = _safe_num(a.get("similarity"))

            num_rel_drop = _rel_drop(num_b, num_a)
            sim_delta = _delta(sim_b, sim_a)

            kind_entry[transform_label] = {
                "num_before": num_b,
                "num_after": num_a,
                "num_rel_drop": num_rel_drop,
                "similarity_before": sim_b,
                "similarity_after": sim_a,
                "similarity_delta": sim_delta
            }

            if num_rel_drop is not None and num_rel_drop > th["primitive_count_rel_drop_threshold"]:
                flags.append(f"{kind}_count_drop")
                notes.append(f"{root.current_lang.get('analysis_notes_primitive_count_drop').get()} "
                             f"{kind}@{transform_label}: −{num_rel_drop*100:.1f}%")

            if sim_delta is not None and sim_delta < -th["primitive_similarity_abs_drop_threshold"]:
                flags.append(f"{kind}_similarity_drop")
                # Prozent statt Absolutwert:
                notes.append(f"{root.current_lang.get('analysis_notes_primitive_similarity_drop').get()} "
                             f"{kind}@{transform_label}: {sim_delta*100:+.1f}%")

        geo_diff[kind] = kind_entry

    if geo_diff:
        diff["geometric_primitives"] = geo_diff

    # =====================================================
    # Zusammenfassung (nur Texte; keine Zahlen nötig)
    # =====================================================
    summary_bits: List[str] = []
    if any(f.endswith("keypoints_drop") for f in flags):
        summary_bits.append(root.current_lang.get("analysis_summary_keypoints_drop").get())
    if any("repeatability_drop" in f for f in flags):
        summary_bits.append(root.current_lang.get("analysis_summary_repeatability_drop").get())
    if any(f.startswith("kd_") and f.endswith("_drop") for f in flags if "repeatability" not in f):
        summary_bits.append(root.current_lang.get("analysis_summary_matching_quality_drop").get())
    if any(f.endswith("_similarity_drop") for f in flags):
        summary_bits.append(root.current_lang.get("analysis_summary_geometric_similarity_drop").get())

    assessment = {
        "summary": summary_bits if summary_bits else [root.current_lang.get("analysis_assessment_no_changes").get()],
        "notes": notes
    }

    return {
        "thresholds_used": dict(th),
        "diff": diff,
        "flags": flags,
        "assessment": assessment,
        "raw": {
            "before": before_res,
            "after": after_res
        }
    }
