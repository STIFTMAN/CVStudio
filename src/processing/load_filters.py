import json


def load() -> dict:
    temp: dict = {}
    with open("./src/assets/filters/default.json", "r", encoding="utf-8") as f:
        temp = json.load(f)
    with open("./src/assets/filters/additional.json", "r", encoding="utf-8") as f:
        temp_data: dict = json.load(f)
        for key in temp_data:
            if key not in temp:
                temp[key] = temp_data
    return temp
