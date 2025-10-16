import json
from pathlib import Path
from src.gui.state.project_file_type import Project_File_Type
import src.gui.state.root as root
from src.gui.state.error import Error
import src.processing.load_action as filters
from pydantic import TypeAdapter, ValidationError
import src.gui.utils.logger as log


def load():
    folder = Path("./src/assets/projects")
    adapter = TypeAdapter(Project_File_Type)
    for file in folder.glob("*.json"):
        name = file.stem
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            try:
                project: Project_File_Type = adapter.validate_python(data)
                root.all_projects[name] = project
            except ValidationError:
                log.log.write(text=f"{Error.INVALID_PROJECT_FILE.value} ({file})", tag="ERROR", modulename=Path(__file__).stem)
    load_filters()


def load_filters():
    root.all_filters = filters.load()


def save_project(name: str, data: Project_File_Type):
    with open("src/assets/projects/" + name + ".json", "w", encoding="utf-8") as f:
        f.write(json.dumps(data))
    root.all_projects[name] = data


def save_filter():
    data = {}
    for key in root.all_filters:
        temp_data = root.all_filters[key]["data"]
        if root.all_filters[key]["type"] == "filter" and isinstance(temp_data, dict):
            if temp_data["settings"]["mutable"]:
                data[key] = root.all_filters[key]
    with open("src/assets/action/additional.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(data))
