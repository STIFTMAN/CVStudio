import json
from pathlib import Path
from src.gui.state.project_file_type import Project_File_Type
import src.gui.state.root as root
from src.gui.utils.project import Project
from ..state.error import Error
import src.processing.load_filters as filters


def load():
    folder = Path("./src/assets/projects")
    for file in folder.glob("*.json"):
        name = file.stem
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if Project.validate(data):
                root.all_projects[name] = data
            else:
                print(Error.INVALID_PROJECT_FILE.value, name)
    load_filters()


def load_filters():
    root.all_filters = filters.load()


def save_project(name: str, data: Project_File_Type):
    with open("src/assets/projects/" + name + ".json", "w", encoding="utf-8") as f:
        f.write(json.dumps(data))
    root.all_projects[name] = data
