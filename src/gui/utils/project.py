from typing import Any
from src.gui.state.project_file_type import Filter_Type, Project_File_Type, empty_project
import src.gui.state.root as root
import re


class Project:
    data: Project_File_Type | None = None
    image = None
    name: str = ""

    temp_images = []

    def get_filternames(self) -> list[str]:
        temp: list[str] = []
        if self.data is not None:
            for key in range(len(self.data["filterqueue"])):
                temp_val = self.data["filterqueue"][key]
                if isinstance(temp_val, str):
                    temp.append(temp_val)
                else:
                    temp.append(temp_val["name"])
        return temp

    @staticmethod
    def get_filterid_by_name(name: str = "") -> str | None:
        for key in root.all_filters:
            if root.all_filters[key]["name"] == name:
                return key
        return None

    def add_filter(self, id: str):
        if self.data is not None:
            self.data["filterqueue"].append(id)

    def get_filter(self) -> list[str]:
        if self.data is not None:
            return self.data["filterqueue"]
        return []

    def ready(self) -> bool:
        if self.data is None:
            return False
        return True

    def image_ready(self) -> bool:
        return self.image is not None

    def load_image(self, img):
        self.image = img
        self.temp_images = []

    def load_data(self, name, data):
        self.data = data
        self.name = name

    def reset(self):
        self.data = None
        self.image = None
        self.name = ""

    def save(self) -> bool:
        if self.data is not None:
            from src.gui.utils.project_loader import save_project
            save_project(self.name, self.data)
            return True
        return False

    @staticmethod
    def get_filter_by_id(id: str) -> Filter_Type | None:
        if id in root.all_filters:
            return root.all_filters[id]
        return None

    @staticmethod
    def validate(data: Any) -> bool:
        return True

    @staticmethod
    def save_filter(id: str, filter: Filter_Type):
        root.all_filters[id] = filter
        import src.gui.utils.project_loader
        src.gui.utils.project_loader.save_filter()

    @staticmethod
    def delete_filter(id: str):
        if root.all_filters[id]["settings"]["mutable"]:
            del root.all_filters[id]

    @staticmethod
    def valid_filename(name: str) -> bool:
        if len(name) <= 0:
            return False
        if name in root.all_projects:
            return False
        elif re.search("^[A-Za-z-_0-9]+$", name) is None:
            return False
        return True

    @staticmethod
    def create(name: str) -> bool:
        if not Project.valid_filename(name):
            return False
        from src.gui.utils.project_loader import save_project
        save_project(name, empty_project)
        root.current_project.load_data(name, empty_project)
        return True
