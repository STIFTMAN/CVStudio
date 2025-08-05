from typing import Any
from src.gui.state.project_file_type import Project_File_Type, template
import src.gui.state.root as root
import re


class Project:
    data: Project_File_Type | None = None
    image = None
    name: str = ""

    temp_images = []

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

    @staticmethod
    def validate(data: Any) -> bool:
        return True

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
        save_project(name, template)
        return True
