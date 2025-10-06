from typing import Literal
from src.processing.basic_stats_type import Basic_Stats
from src.processing.image_compare_stats import analyze_stats_delta
from src.processing.stats import compute_image_stats_global
from src.processing.image_compare_feature_stats import analyze_feature_tests_delta_from_results
from src.processing.test.feature_test import run_selected_feature_tests
from src.processing.action_handeling import feature_mode
import numpy as np

f_mode = Literal[feature_mode]


def quick_test(image_before: np.ndarray, temp_images: list[np.ndarray], stats_list: list[Basic_Stats]) -> dict:

    features: list[f_mode] = []  # type: ignore
    end_index: int = -1
    for i, key in enumerate(stats_list):
        if key["action"]["type"] == "feature" and key["action"]["data"] in feature_mode:
            features.append(key["action"]["data"])
            if end_index == -1:
                end_index = i
    basic_before = compute_image_stats_global(image_before)
    if end_index - 1 < 0:
        basic_after = compute_image_stats_global(image_before)
    else:
        basic_after = compute_image_stats_global(temp_images[end_index])
    basic_result = analyze_stats_delta(basic_before, basic_after)
    time_all: float = 0.0
    for item in stats_list:
        time_all += item["time"]
    b_stats: Basic_Stats = {
        "time": time_all,
        "action": {
            "type": "all",
            "data": "-"
        },
        "extended_stats": basic_result
    }

    summary = {
        "basic": b_stats,
        "feature": None
    }

    if len(features) > 0:
        feature_before = run_selected_feature_tests(image_before, features)
        if end_index - 1 < 0:
            feature_after = run_selected_feature_tests(image_before, features)
        else:
            feature_after = run_selected_feature_tests(temp_images[end_index], features)
        feature_result = analyze_feature_tests_delta_from_results(feature_before, feature_after)

        summary["feature"] = feature_result

    return summary
