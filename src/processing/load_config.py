import json
from typing import cast
from src.processing.config_type import Config_Processing_Type


def load() -> Config_Processing_Type:
    data = {
        "feature": {},
        "stats_threshold": {},
        "feature_stats_threshold": {},
        "tests": {}
    }
    modules = ["harris", "surf", "sift", "orb", "fast", "hough_lines", "hough_circle", "hough_rectangle"]
    for key in modules:
        with open(f"./src/assets/action/config/feature/{key}.json", "r", encoding="utf-8") as f:
            data["feature"][key] = json.load(f)

    with open("./src/assets/action/config/stats_threshold.json", "r", encoding="utf-8") as f:
        data["stats_threshold"] = json.load(f)

    with open("./src/assets/action/config/feature_stats_threshold.json", "r", encoding="utf-8") as f:
        data["feature_stats_threshold"] = json.load(f)

    with open("./src/assets/action/config/tests.json", "r", encoding="utf-8") as f:
        data["tests"] = json.load(f)

    return cast(Config_Processing_Type, data)
