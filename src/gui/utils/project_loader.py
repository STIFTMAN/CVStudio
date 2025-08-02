import json
from pathlib import Path
import src.gui.state.root as root
from src.gui.utils.project import Project
from ..state.error import Error


def load():
    folder = Path("./src/assets/projects")
    for file in folder.glob("*.json"):
        name = file.stem
        with open(file, "r", encoding="utf-8") as f:
            if Project.validate(json.load(f)):
                root.all_projects[name]
            else:
                print(Error.INVALID_PROJECT_FILE.value, name)
