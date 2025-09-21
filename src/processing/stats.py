import numpy as np
from typing import Dict, Any, Tuple
from src.gui.state.error import Error


def compute_image_stats_global(
    image: np.ndarray,
    nbins: int = 256,
    compute_frequency: bool = True
) -> Dict[str, Any]:
    """
    Compute *global* image statistics only (no local neighborhood operators).
    - Supports HW (grayscale), HWC (color), and CHW layouts.
    - NumPy-only implementation.
    - Many metrics are computed on a grayscale/luminance representation in the range [0, 1].

    Parameters
    ----------
    image : np.ndarray
        Input image (HW / HWC / CHW), float or integer dtype.
    nbins : int
        Number of histogram bins for entropy/Otsu on [0, 1].
    compute_frequency : bool
        Whether to compute global FFT-based frequency metrics.

    Returns
    -------
    Dict[str, Any]
        Dictionary of global statistics (schema unchanged for compatibility).
    """

    # ---------- Helpers ----------

    def detect_image_layout(arr: np.ndarray) -> str:
        if arr.ndim == 2:
            return "HW"
        if arr.ndim == 3:
            h, w, c = arr.shape
            if c in (1, 3, 4):
                return "HWC"
            if arr.shape[0] in (1, 3, 4):
                return "CHW"
        return "unknown"

    def ensure_hwc_layout(arr: np.ndarray) -> np.ndarray:
        layout = detect_image_layout(arr)
        if layout == "HW":
            return arr[..., None]
        if layout == "HWC":
            return arr
        if layout == "CHW":
            return np.transpose(arr, (1, 2, 0))
        raise ValueError(f"{Error.UNSUPPORTED_IMAGE_SHAPE.value}: {arr.shape}")

    def to_float64_array(arr: np.ndarray) -> np.ndarray:
        return arr.astype(np.float64, copy=False)

    def normalize_to_unit_range(arr: np.ndarray) -> Tuple[np.ndarray, Tuple[float, float]]:
        """
        Map image to [0, 1].
        - Integer: scale by dtype min/max.
        - Float: if already in [0, 1], keep; else min-max normalize.
        Returns (normalized_array, (assumed_input_min, assumed_input_max)).
        """
        if not np.issubdtype(arr.dtype, np.floating):
            dtype_info = np.iinfo(arr.dtype)
            in_min, in_max = dtype_info.min, dtype_info.max
            arr64 = to_float64_array(arr)
            return (arr64 - in_min) / (in_max - in_min), (float(in_min), float(in_max))

        arr64 = to_float64_array(arr)
        vmin, vmax = float(arr64.min()), float(arr64.max())
        if vmin >= 0.0 and vmax <= 1.0:
            return arr64, (0.0, 1.0)
        if vmax > vmin:
            return (arr64 - vmin) / (vmax - vmin), (vmin, vmax)
        return np.zeros_like(arr64), (vmin, vmax)

    def rgb_like_to_luminance01(rgb01: np.ndarray) -> np.ndarray:
        """Return luminance from HWC image in [0, 1]. If single channel, return it."""
        if rgb01.shape[2] == 1:
            return rgb01[..., 0]
        r, g, b = rgb01[..., 0], rgb01[..., 1], rgb01[..., 2]
        return 0.2989 * r + 0.5870 * g + 0.1140 * b

    def histogram_and_entropy_bits(gray01: np.ndarray, bins: int) -> Tuple[np.ndarray, float]:
        hist_counts, _ = np.histogram(gray01, bins=bins, range=(0.0, 1.0))
        p = hist_counts.astype(np.float64)
        p = p / (p.sum() + 1e-12)
        entropy = -np.sum(p * np.log2(np.maximum(p, 1e-300)))
        return hist_counts, float(entropy)

    def compute_otsu_threshold01(gray01: np.ndarray, bins: int) -> float:
        hist_counts, _ = np.histogram(gray01, bins=bins, range=(0.0, 1.0))
        p = hist_counts.astype(np.float64)
        p /= (p.sum() + 1e-12)
        cumulative_prob = np.cumsum(p)
        bin_centers = (np.arange(bins) + 0.5) / bins
        cumulative_mean = np.cumsum(p * bin_centers)
        total_mean = cumulative_mean[-1]
        between_var = (total_mean * cumulative_prob - cumulative_mean) ** 2 / (cumulative_prob * (1 - cumulative_prob) + 1e-12)
        best_k = int(np.nanargmax(between_var))
        return float((best_k + 0.5) / bins)

    # ---------- Preprocessing ----------

    image_hwc = ensure_hwc_layout(image)
    height, width, channels = image_hwc.shape

    # Per-channel stats on original value scale (but cast to float64)
    image_float64 = to_float64_array(image_hwc)
    per_channel_stats = {
        "min": image_float64.min(axis=(0, 1)).tolist(),
        "max": image_float64.max(axis=(0, 1)).tolist(),
        "mean": image_float64.mean(axis=(0, 1)).tolist(),
        "var": image_float64.var(axis=(0, 1)).tolist(),
        "std": image_float64.std(axis=(0, 1)).tolist(),
    }

    # Channel covariance/correlation (global)
    channel_correlation_matrix = channel_covariance_matrix = None
    if channels >= 2:
        flattened_pixels = image_float64.reshape(-1, channels)
        covariance = np.cov(flattened_pixels, rowvar=False)
        stddev = np.sqrt(np.clip(np.diag(covariance), 0.0, np.inf)) + 1e-12
        correlation = covariance / (stddev[:, None] * stddev[None, :])
        channel_covariance_matrix = covariance.tolist()
        correlation = np.clip(correlation, -1.0, 1.0)
        channel_correlation_matrix = correlation.tolist()

    # Normalize to [0, 1] for histogram/threshold/color metrics
    image_unit_range, input_scale_info = normalize_to_unit_range(image_hwc)
    luminance01 = rgb_like_to_luminance01(image_unit_range)

    # ---------- Intensity / Histogram (global) ----------

    min_intensity = float(luminance01.min())
    max_intensity = float(luminance01.max())
    mean_intensity = float(luminance01.mean())
    median_intensity = float(np.median(luminance01))
    std_intensity = float(luminance01.std())
    var_intensity = float(luminance01.var())
    intensity_range = max_intensity - min_intensity

    percentiles = np.percentile(luminance01, [1, 5, 50, 95, 99])
    p01, p05, p50, p95, p99 = [float(v) for v in percentiles]

    # Skewness / (excess) kurtosis
    if std_intensity > 0:
        zscores = (luminance01 - mean_intensity) / std_intensity
        skewness = float((zscores ** 3).mean())
        kurtosis_excess = float((zscores ** 4).mean() - 3.0)
    else:
        skewness = 0.0
        kurtosis_excess = -3.0

    histogram_counts_256, entropy_bits = histogram_and_entropy_bits(luminance01, nbins)
    otsu_threshold_01 = compute_otsu_threshold01(luminance01, nbins)

    clip_low_fraction = clip_high_fraction = None
    if input_scale_info == (0.0, 1.0):
        clip_low_fraction = float((luminance01 <= 0.0).mean())
        clip_high_fraction = float((luminance01 >= 1.0).mean())

    # ---------- Color (global) ----------

    colorfulness_hs = None
    if channels >= 3:
        rgb_0_255 = np.clip(image_unit_range[..., :3] * 255.0, 0.0, 255.0)
        red, green, blue = [rgb_0_255[..., i].astype(np.float64) for i in range(3)]
        rg = red - green
        yb = 0.5 * (red + green) - blue
        colorfulness_hs = float(np.sqrt(rg.var() + yb.var()) + 0.3 * (rg.std() + yb.std()))

    # ---------- Frequency domain (global) ----------

    high_frequency_energy_ratio = spectral_centroid = autocorrelation_peak_offcenter = None
    if compute_frequency:
        fourier = np.fft.fftshift(np.fft.fft2(luminance01))
        power_spectrum = np.abs(fourier) ** 2

        center_y, center_x = height // 2, width // 2
        y_indices, x_indices = np.ogrid[:height, :width]
        radius_sq = (y_indices - center_y) ** 2 + (x_indices - center_x) ** 2

        low_freq_radius = max(1, min(height, width) // 8)
        low_frequency_mask = radius_sq <= (low_freq_radius ** 2)

        high_frequency_energy_ratio = float(
            power_spectrum[~low_frequency_mask].sum() / (power_spectrum.sum() + 1e-12)
        )

        radial_distance = np.sqrt(radius_sq)
        radial_distance_norm = radial_distance / (radial_distance.max() + 1e-12)
        spectral_centroid = float((power_spectrum * radial_distance_norm).sum() / (power_spectrum.sum() + 1e-12))

        autocorrelation = np.real(np.fft.ifft2(np.abs(fourier) ** 2))
        off_center_mask = np.ones_like(autocorrelation, dtype=bool)
        off_center_mask[0, 0] = False
        autocorrelation_peak_offcenter = float(
            autocorrelation[off_center_mask].max() / (autocorrelation[0, 0] + 1e-12)
        )

    # ---------- Pack results (schema unchanged) ----------

    stats: Dict[str, Any] = {
        "shape": (height, width, channels),
        "layout": detect_image_layout(image),
        "dtype": str(image.dtype),
        "scale_info": {"assumed_input_min_max": input_scale_info},
        "intensity_gray01": {
            "min": min_intensity,
            "max": max_intensity,
            "range": intensity_range,
            "mean": mean_intensity,
            "median": median_intensity,
            "std": std_intensity,
            "var": var_intensity,
            "q01": p01,
            "q05": p05,
            "q50": p50,
            "q95": p95,
            "q99": p99,
            "skewness": skewness,
            "kurtosis_excess": kurtosis_excess,
            "entropy_bits": float(entropy_bits),
            "hist_counts": histogram_counts_256.tolist(),
            "hist_range": [0.0, 1.0],
            "otsu_threshold_01": float(otsu_threshold_01),
            "clip_low_frac": clip_low_fraction,
            "clip_high_frac": clip_high_fraction,
        },
        "per_channel": per_channel_stats,
        "channel_covariance": channel_covariance_matrix,
        "channel_correlation": channel_correlation_matrix,
        "color": {
            "colorfulness": colorfulness_hs
        },
        "frequency": {
            "enabled": bool(compute_frequency),
            "high_freq_ratio": high_frequency_energy_ratio,
            "spectral_centroid": spectral_centroid,
            "autocorr_peak_offcenter": autocorrelation_peak_offcenter,
        },
    }

    return stats
