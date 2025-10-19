import customtkinter
import numpy
from src.processing.basic_stats_type import Basic_Stats
from src.processing.test.quick_test import quick_test
from src.gui.state.project_file_type import Action_Queue_Obj_Type, Action_Type, Filter_Type, Project_File_Type, empty_project
import src.processing.action_handeling as action_processing
import src.gui.state.root as root
import re
import json
import hashlib
import numpy.typing as npt


class Project:
    data: Project_File_Type | None = None
    image: numpy.ndarray | None = None
    name: str = ""

    progress: customtkinter.DoubleVar | None = None
    progress_test: customtkinter.DoubleVar | None = None
    action_queue: list[Action_Queue_Obj_Type] = []
    temp_images: list[numpy.typing.NDArray[numpy.uint8 | numpy.float32]] = []
    override_index = -1
    temp_stats: list[Basic_Stats] = []
    d_image: npt.NDArray[numpy.uint8] | None = None
    analyse_list = []
    test_results = None
    running: bool = False
    canceling: bool = False

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

    def reset_action_queue(self):
        self.action_queue = []
        self.temp_images = []
        self.temp_stats = []
        self.override_index = -1
        self.d_image = None
        self.running = False
        self.canceling = False

    def quick_test(self):
        if self.image is not None and len(self.temp_images) > 0:
            self.test_results = quick_test(self.image, self.temp_images, self.temp_stats)

    def apply_action_queue(self):
        assert root.status is not None
        self.override_index = -1
        if not self.data:
            return
        if len(self.data["filterqueue"]) == 0:
            self.reset_action_queue()
            root.status.set(root.current_lang.get("project_apply_action_queue_status_empty_queue").get())
            return
        if self.running is False:
            self.running = True
            self.canceling = False
        else:
            self.canceling = True
            return
        new_action_queue: list[Action_Queue_Obj_Type] = []
        for key in self.data["filterqueue"]:
            if key not in root.all_filters:
                return
            action = root.all_filters[key]
            json_data = json.dumps(action["data"], sort_keys=True, separators=(',', ':'))
            dict_obj: Action_Queue_Obj_Type = {
                "data": action,
                "hash": hashlib.sha256(json_data.encode('utf-8')).hexdigest()
            }
            new_action_queue.append(dict_obj)
        if len(self.action_queue) < len(new_action_queue):
            self.override_index = len(self.action_queue) - 1
        elif len(self.action_queue) > len(new_action_queue):
            self.action_queue = self.action_queue[0:len(new_action_queue) - 1]
            self.temp_images = self.temp_images[0:len(new_action_queue) - 1]
            self.temp_stats = self.temp_stats[0:len(new_action_queue) - 1]
        for index, obj in enumerate(new_action_queue):
            if len(self.action_queue) - 1 < index:
                self.override_index = index
                break
            if obj["hash"] != self.action_queue[index]["hash"]:
                self.override_index = index
                break
        if self.override_index == -1:
            root.status.set(root.current_lang.get("project_apply_action_queue_status_no_changes").get())
            self.running = False
            self.canceling = False
            return
        self.action_queue = new_action_queue
        self.temp_images = self.temp_images[0:min(self.override_index, len(self.temp_images))]
        self.temp_stats = self.temp_stats[0:min(self.override_index, len(self.temp_stats))]
        self.d_image = None
        if self.progress:
            self.progress.set(0.0)
        for i in range(self.override_index, len(self.action_queue)):
            src_img: numpy.ndarray | None = None
            if i == 0:
                src_img = self.image
            else:
                src_img = self.temp_images[i - 1]
            if src_img is None:
                return
            action_data = self.action_queue[i]["data"]
            if action_data["type"] == "filter":
                filter_data = action_data['data']
                assert not isinstance(filter_data, str)
                root.status.set(f"( {i+1} / {len(self.action_queue)} ) - {filter_data['name']}")
            else:
                root.status.set(f"( {i+1} / {len(self.action_queue)} ) - {action_data['data']}")
            new_data = action_processing.apply_action(src_img, action_data, draw_image=self.d_image)
            if new_data[2] is None or i + 1 < len(self.action_queue):
                self.temp_images.append(new_data[0])
            else:
                self.temp_images.append(new_data[2])
            self.temp_stats.append(new_data[1])
            self.d_image = new_data[2]
            if self.progress:
                self.progress.set((i + 1) / len(self.action_queue))
            if self.canceling:
                self.reset_action_queue()
                self.apply_action_queue()
                break
        if self.progress:
            root.status.set(root.current_lang.get("project_apply_action_queue_status_done").get())
            if self.progress.get() != 1.0:
                self.progress.set(1.0)
        self.running = False

    def set_progress(self, p: customtkinter.DoubleVar):
        self.progress = p

    def set_progress_test(self, p: customtkinter.DoubleVar):
        self.progress_test = p

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

    def load_image(self, img: numpy.ndarray | None):
        self.image = img
        self.temp_images = []

    def load_data(self, name, data):
        self.data = data
        self.name = name

    def reset(self):
        self.data = None
        self.image = None
        self.name = ""
        self.reset_action_queue()

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
