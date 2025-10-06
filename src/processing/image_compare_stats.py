import numpy as np
from typing import Dict, Any, Optional, List
import src.gui.state.root as root

# Global thresholds for flagging unusual changes (adjust centrally as needed)
ALERT_THRESHOLDS: Dict[str, float] = {
    "mean_abs_delta_threshold": 0.02,                # absolute Δ of gray mean in [0..1]
    "std_relative_change_threshold": 0.15,           # relative Δ of gray std (±15%)
    "entropy_bits_delta_threshold": 0.10,            # Δ entropy in bits
    "js_divergence_threshold": 0.05,                 # Jensen–Shannon divergence (histogram shift)
    "highfreq_ratio_delta_threshold": 0.05,          # Δ high-frequency energy ratio
    "colorfulness_delta_threshold": 5.0,             # Δ Hasler–Süsstrunk colorfulness
    "channel_corr_abs_delta_threshold": 0.10,        # max |Δ| in channel correlation matrix
    "clipping_fraction_delta_threshold": 0.01        # Δ clipping fraction (1%)
}


def analyze_stats_delta(stats_before: Dict[str, Any], stats_after: Dict[str, Any]) -> Dict[str, Any]:

    def get_nested(d: Dict[str, Any], keys: List[str], default=None):
        node = d
        for k in keys:
            if not (isinstance(node, dict) and k in node):
                return default
            node = node[k]
        return node

    def jensen_shannon_divergence_from_hist_counts(hist_counts_a: List[float], hist_counts_b: List[float]) -> float:
        p = np.asarray(hist_counts_a, dtype=np.float64)
        p /= (p.sum() + 1e-12)
        q = np.asarray(hist_counts_b, dtype=np.float64)
        q /= (q.sum() + 1e-12)
        m = 0.5 * (p + q)
        kl_pm = np.sum(p * np.log2(np.maximum(p, 1e-300) / np.maximum(m, 1e-300)))
        kl_qm = np.sum(q * np.log2(np.maximum(q, 1e-300) / np.maximum(m, 1e-300)))
        return float(0.5 * (kl_pm + kl_qm))

    def safe_numeric_delta(a: Optional[float], b: Optional[float]) -> Optional[float]:
        return None if (a is None or b is None) else float(b - a)

    def list_elementwise_delta(list_a: List[float], list_b: List[float]) -> List[float]:
        n = min(len(list_a), len(list_b))
        if n == 0:
            return []
        return (np.asarray(list_b[:n], dtype=np.float64) - np.asarray(list_a[:n], dtype=np.float64)).tolist()

    gray_stats_before = get_nested(stats_before, ["intensity_gray01"], {}) or {}
    gray_stats_after = get_nested(stats_after, ["intensity_gray01"], {}) or {}

    std_before = float(gray_stats_before.get("std", 0.0) or 0.0)
    std_after = float(gray_stats_after.get("std", 0.0) or 0.0)

    hist_counts_before = (gray_stats_before.get("hist_counts") or gray_stats_before.get("histogram") or [])
    hist_counts_after = (gray_stats_after.get("hist_counts") or gray_stats_after.get("histogram") or [])

    intensity_deltas = {
        "mean_delta": float((gray_stats_after.get("mean", 0.0) or 0.0) - (gray_stats_before.get("mean", 0.0) or 0.0)),
        "std_delta": float(std_after - std_before),
        "std_rel_change": float((std_after - std_before) / (std_before + 1e-12)),
        "entropy_delta_bits": float((gray_stats_after.get("entropy_bits", 0.0) or 0.0) - (gray_stats_before.get("entropy_bits", 0.0) or 0.0)),
        "q05_delta": float((gray_stats_after.get("q05", 0.0) or 0.0) - (gray_stats_before.get("q05", 0.0) or 0.0)),
        "q95_delta": float((gray_stats_after.get("q95", 0.0) or 0.0) - (gray_stats_before.get("q95", 0.0) or 0.0)),
        "otsu_threshold_delta": float((gray_stats_after.get("otsu_threshold_01", 0.0) or 0.0) - (gray_stats_before.get("otsu_threshold_01", 0.0) or 0.0)),
        "js_divergence_hist": (jensen_shannon_divergence_from_hist_counts(hist_counts_before, hist_counts_after) if (hist_counts_before and hist_counts_after) else None),
        "clip_low_delta": safe_numeric_delta(gray_stats_before.get("clip_low_frac"), gray_stats_after.get("clip_low_frac")),
        "clip_high_delta": safe_numeric_delta(gray_stats_before.get("clip_high_frac"), gray_stats_after.get("clip_high_frac")),
    }

    per_channel_before = get_nested(stats_before, ["per_channel"], {}) or {}
    per_channel_after = get_nested(stats_after, ["per_channel"], {}) or {}

    per_channel_deltas = {
        "channels_before": len(per_channel_before.get("mean", []) or []),
        "channels_after": len(per_channel_after.get("mean", []) or []),
        "mean_delta": list_elementwise_delta(per_channel_before.get("mean", []) or [], per_channel_after.get("mean", []) or []),
        "var_delta": list_elementwise_delta(per_channel_before.get("var", []) or [], per_channel_after.get("var", []) or []),
        "std_delta": list_elementwise_delta(per_channel_before.get("std", []) or [], per_channel_after.get("std", []) or []),
        "min_delta": list_elementwise_delta(per_channel_before.get("min", []) or [], per_channel_after.get("min", []) or []),
        "max_delta": list_elementwise_delta(per_channel_before.get("max", []) or [], per_channel_after.get("max", []) or []),
    }

    # ---------- Colorfulness delta ----------
    colorfulness_before = get_nested(stats_before, ["color", "colorfulness"])
    colorfulness_after = get_nested(stats_after, ["color", "colorfulness"])
    assert (colorfulness_before is None or isinstance(colorfulness_before, float)) and (colorfulness_after is None or isinstance(colorfulness_after, float))
    colorfulness_delta = safe_numeric_delta(colorfulness_before, colorfulness_after)

    # ---------- Channel correlation changes ----------
    corr_matrix_before = get_nested(stats_before, ["channel_correlation"])
    corr_matrix_after = get_nested(stats_after, ["channel_correlation"])

    channel_correlation_delta = None
    channel_correlation_alerts: List[Dict[str, Any]] = []

    if isinstance(corr_matrix_before, list) and isinstance(corr_matrix_after, list):
        corr_before_np = np.asarray(corr_matrix_before, dtype=np.float64)
        corr_after_np = np.asarray(corr_matrix_after, dtype=np.float64)
        if corr_before_np.shape == corr_after_np.shape and corr_before_np.size > 0:
            corr_delta_np = corr_after_np - corr_before_np
            channel_correlation_delta = {
                "fro_norm": float(np.linalg.norm(corr_delta_np)),
                "max_abs_delta": float(np.max(np.abs(corr_delta_np))),
                "matrix_delta": corr_delta_np.tolist()
            }
            idx_pairs = np.argwhere(
                np.abs(corr_delta_np) > ALERT_THRESHOLDS["channel_corr_abs_delta_threshold"]
            )
            for i, j in idx_pairs:
                if int(i) < int(j):  # report each pair once
                    channel_correlation_alerts.append({
                        "channel_pair": [int(i), int(j)],
                        "delta_corr": float(corr_delta_np[i, j])
                    })

    freq_before = get_nested(stats_before, ["frequency"], {}) or {}
    freq_after = get_nested(stats_after, ["frequency"], {}) or {}

    frequency_delta = None
    if freq_before.get("enabled") and freq_after.get("enabled"):
        def delta_or_none(key: str) -> Optional[float]:
            a, b = freq_before.get(key), freq_after.get(key)
            return None if (a is None or b is None) else float(b - a)
        frequency_delta = {
            "high_freq_ratio_delta": delta_or_none("high_freq_ratio"),
            "spectral_centroid_delta": delta_or_none("spectral_centroid"),
            "autocorr_peak_offcenter_delta": delta_or_none("autocorr_peak_offcenter"),
        }

    flags: List[str] = []
    notes: List[str] = []

    if abs(intensity_deltas["mean_delta"]) > ALERT_THRESHOLDS["mean_abs_delta_threshold"]:
        flags.append("mean_shift")
        notes.append(f"{root.current_lang.get('analysis_notes_mean_shift').get()} {intensity_deltas['mean_delta']:+.3f}")

    if abs(intensity_deltas["std_rel_change"]) > ALERT_THRESHOLDS["std_relative_change_threshold"]:
        flags.append("contrast_change")
        notes.append(f"{root.current_lang.get('analysis_notes_contrast_change').get()} {intensity_deltas['std_rel_change']*100:+.1f}%")

    if abs(intensity_deltas["entropy_delta_bits"]) > ALERT_THRESHOLDS["entropy_bits_delta_threshold"]:
        flags.append("entropy_change")
        notes.append(f"{root.current_lang.get('analysis_notes_entropy_change').get()} {intensity_deltas['entropy_delta_bits']:+.2f} bits")

    js_value = intensity_deltas["js_divergence_hist"]
    if js_value is not None and js_value > ALERT_THRESHOLDS["js_divergence_threshold"]:
        flags.append("histogram_shift")
        notes.append(f"{root.current_lang.get('analysis_notes_histogram_shift').get()} (JS ≈ {js_value:.3f}).")

    low_clip_delta = intensity_deltas["clip_low_delta"]
    high_clip_delta = intensity_deltas["clip_high_delta"]
    if low_clip_delta is not None and abs(low_clip_delta) > ALERT_THRESHOLDS["clipping_fraction_delta_threshold"]:
        flags.append("black_clipping_change")
        notes.append(f"{root.current_lang.get('analysis_notes_black_clipping_change').get()} {low_clip_delta:+.3%}")
    if high_clip_delta is not None and abs(high_clip_delta) > ALERT_THRESHOLDS["clipping_fraction_delta_threshold"]:
        flags.append("white_clipping_change")
        notes.append(f"{root.current_lang.get('analysis_notes_white_clipping_change').get()} {high_clip_delta:+.3%}.")

    if (colorfulness_delta is not None) and (abs(colorfulness_delta) > ALERT_THRESHOLDS["colorfulness_delta_threshold"]):
        flags.append("colorfulness_change")
        notes.append(f"{root.current_lang.get('analysis_notes_colorfulness_change').get()} {colorfulness_delta:+.2f}.")

    if (channel_correlation_delta is not None and channel_correlation_delta["max_abs_delta"] > ALERT_THRESHOLDS["channel_corr_abs_delta_threshold"]):
        flags.append("channel_correlation_change")
        notes.append(f"{root.current_lang.get('analysis_notes_channel_correlation_change').get()} {channel_correlation_delta['max_abs_delta']:.2f}")

    if frequency_delta is not None:
        hf_delta = frequency_delta.get("high_freq_ratio_delta")
        if hf_delta is not None:
            if hf_delta < -ALERT_THRESHOLDS["highfreq_ratio_delta_threshold"]:
                flags.append("likely_smoothing")
                notes.append(f"{root.current_lang.get('analysis_notes_less_high_frequency').get()} {hf_delta:+.3f} {root.current_lang.get('analysis_notes_likely_smoothing').get()}")
            elif hf_delta > ALERT_THRESHOLDS["highfreq_ratio_delta_threshold"]:
                flags.append("likely_sharpening_or_noise")
                notes.append(f"{root.current_lang.get('analysis_notes_more_high_frequency').get()} {hf_delta:+.3f} {root.current_lang.get('analysis_notes_likely_sharpening_or_noise').get()}")

    # Short textual summary (German strings intentionally unchanged)
    summary_messages = []
    if "likely_smoothing" in flags:
        summary_messages.append(root.current_lang.get("analysis_summary_likely_smoothing").get())
    if "likely_sharpening_or_noise" in flags:
        summary_messages.append(root.current_lang.get("analysis_summary_likely_sharpening_or_noise").get())
    if "mean_shift" in flags:
        summary_messages.append(root.current_lang.get("analysis_summary_mean_shift").get())
    if "contrast_change" in flags:
        summary_messages.append(root.current_lang.get("analysis_summary_contrast_change").get())
    if "colorfulness_change" in flags:
        summary_messages.append(root.current_lang.get("analysis_summary_colorfulness_change").get())
    if "black_clipping_change" in flags or "white_clipping_change" in flags:
        summary_messages.append(root.current_lang.get("analysis_summary_clipping_change").get())
    if "channel_correlation_change" in flags:
        summary_messages.append(root.current_lang.get("analysis_summary_clipping_change").get())

    assessment = {
        "summary": summary_messages if summary_messages else [root.current_lang.get("analysis_assessment_no_changes").get()],
        "notes": notes
    }

    # ---------- Assemble result (schema unchanged) ----------
    result: Dict[str, Any] = {
        "thresholds_used": dict(ALERT_THRESHOLDS),
        "meta": {
            "before_shape": stats_before.get("shape"),
            "after_shape": stats_after.get("shape"),
            "before_dtype": stats_before.get("dtype"),
            "after_dtype": stats_after.get("dtype"),
            "before_layout": stats_before.get("layout"),
            "after_layout": stats_after.get("layout"),
        },
        "diff": {
            "intensity_gray01": intensity_deltas,
            "per_channel": per_channel_deltas,
            "color": {"colorfulness_delta": colorfulness_delta},
            "channel_correlation_delta": channel_correlation_delta,
            "channel_correlation_alerts": channel_correlation_alerts,
            "frequency_delta": frequency_delta
        },
        "flags": flags,
        "raw": {
            "before": stats_before,
            "after": stats_after
        },
        "assessment": assessment
    }
    return result
