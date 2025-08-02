from typing import Any


class Project:
    json: dict | None = None
    image = None

    def get_json(self, data):
        self.json = data

    def reset(self):
        pass

    @staticmethod
    def validate(data: Any) -> bool:
        return True
