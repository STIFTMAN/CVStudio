from typing import Any
from src.gui.state.project_file_type import Action_Type, Filter_Type, Project_File_Type, empty_project
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
            temp = root.all_filters[key]
            if isinstance(temp["data"], dict) and temp["data"]["name"] == name:
                return key
        return None

    def add_filter(self, id: str):
        if self.data is not None:
            self.data["filterqueue"].append(id)

    def get_queue(self) -> list[str]:
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
    def get_action_by_id(id: str) -> Action_Type | None:
        if id in root.all_filters:
            return root.all_filters[id]
        return None

    @staticmethod
    def validate(data: Any) -> bool:
        return True

    @staticmethod
    def save_filter(id: str, filter: Filter_Type):
        root.all_filters[id] = {"type": "filter", "data": filter}
        import src.gui.utils.project_loader
        src.gui.utils.project_loader.save_filter()

    def count_ids(self, id: str) -> list[int]:
        temp = []
        if self.data:
            for key in range(len(self.data["filterqueue"])):
                if self.data["filterqueue"][key] == id:
                    temp.append(key)
        return temp

    def delete_filter(self, id: str, index: int):
        data = root.all_filters[id]["data"]
        if isinstance(data, dict) and data["settings"]["mutable"]:
            if self.data:
                if index >= 0 and index < len(self.data["filterqueue"]) and id == self.data["filterqueue"][index]:
                    del self.data["filterqueue"][index]
                    self.save()
            used = False
            for key in root.all_projects:
                for f_key in root.all_projects[key]["filterqueue"]:
                    if f_key == id:
                        used = True
                        break
                if used:
                    break
            if not used:
                del root.all_filters[id]
                import src.gui.utils.project_loader
                src.gui.utils.project_loader.save_filter()

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
