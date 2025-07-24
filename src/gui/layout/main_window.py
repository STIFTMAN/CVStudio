from src.gui.layout import filterqueue_window
from ..utils.config_loader import get_setting
from ..state.root import app
from ..components.CTKDropdownmenu import CTKDropdownmenu

frame: CTKDropdownmenu | None = None


def msg1():
    print("msg1")


def build():
    window_size = get_setting("window_size")["main"]
    screen_coords = (int((app.winfo_screenwidth()-window_size[0])/2), int((app.winfo_screenheight()-window_size[1])/2))

    app.geometry(f"{window_size[0]}x{window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")

    frame = CTKDropdownmenu(master=app)
    frame.add("Datei", "Speichere Endbild", msg1)
    frame.add("Datei", "Speichere Alle Bilder", msg1)
    frame.addButton("Filterqueue", filterqueue_window.build)
    frame.addButton("Testing", msg1)
    frame.add("Einstellungen", "Aussehen", msg1)
    frame.add("Einstellungen", "Tastenbelegungen", msg1)
    frame.add("Einstellungen", "Hilfe", msg1)
    frame.add("Einstellungen", "About", msg1)
    frame.pack(fill="x", side="top")
    frame.outside_tracking(app)
