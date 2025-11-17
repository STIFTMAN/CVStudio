import json

from src.gui.state.project_file_type import Action_Type


def load() -> dict:
    temp: dict[str, Action_Type] = {}

    with open("./src/assets/action/default_filter.json", "r", encoding="utf-8") as f:
        temp = json.load(f)

    with open("./src/assets/action/default_operation.json", "r", encoding="utf-8") as f:
        temp_data: dict = json.load(f)
        for key in temp_data:
            if key not in temp:
                temp[key] = temp_data[key]

    with open("./src/assets/action/default_feature.json", "r", encoding="utf-8") as f:
        temp_data: dict = json.load(f)
        for key in temp_data:
            if key not in temp:
                temp[key] = temp_data[key]

    with open("./src/assets/action/additional.json", "r", encoding="utf-8") as f:
        temp_data: dict = json.load(f)
        for key in temp_data:
            if key not in temp:
                temp[key] = temp_data[key]

    with open("./src/assets/action/default_pipeline.json", "r", encoding="utf-8") as f:
        temp_data: dict = json.load(f)
        for key in temp_data:
            if key not in temp:
                temp[key] = temp_data[key]

    return temp
