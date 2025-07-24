import customtkinter


class StringList:
    data: dict[str, customtkinter.StringVar] = {}

    def change(self, lang: dict[str, str]):
        for key in lang:
            self.add(key, lang[key])

    def get(self, key: str) -> customtkinter.StringVar:
        return self.data[key]

    def add(self, key: str, value: str = ""):
        if key not in self.data:
            self.data[key] = customtkinter.StringVar(value=value)
        else:
            self.data[key].set(value)
