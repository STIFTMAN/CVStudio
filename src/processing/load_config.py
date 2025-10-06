import json
from typing import cast
from src.processing.config_type import Config_Processing_Type


def load() -> Config_Processing_Type:
    data = {}
    modules = ["harris", "surf", "sift", "orb", "fast", "hough_lines", "hough_circle", "hough_rectangle"]
    for key in modules:
        with open(f"./src/assets/action/config/feature/{key}.json", "r", encoding="utf-8") as f:
            data[key] = json.load(f)

    return cast(Config_Processing_Type, data)
