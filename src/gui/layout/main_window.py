from src.gui.layout import filterqueue_window
from ..utils.config_loader import get_setting
from ..state.root import app, current_lang
from ..components.CTKDropdownmenu import CTKDropdownmenu

frame: CTKDropdownmenu | None = None


def msg1():
    print("msg1")


def build():
    window_size = get_setting("window_size")["main"]
    screen_coords = (int((app.winfo_screenwidth() - window_size[0]) / 2), int((app.winfo_screenheight() - window_size[1]) / 2))

    app.geometry(f"{window_size[0]}x{window_size[1]}+{screen_coords[0]}+{screen_coords[1]}")

    frame = CTKDropdownmenu(master=app)
    frame.add("main_window_ctkdropdownmenu_file_save", current_lang.get("main_window_ctkdropdownmenu_file"), current_lang.get("main_window_ctkdropdownmenu_file_save"), msg1)
    frame.add("main_window_ctkdropdownmenu_file_save", current_lang.get("main_window_ctkdropdownmenu_file"), current_lang.get("main_window_ctkdropdownmenu_file_save_all"), msg1)
    frame.addButton("main_window_ctkdropdownmenu_filterqueue", current_lang.get("main_window_ctkdropdownmenu_filterqueue"), filterqueue_window.build)
    frame.addButton("main_window_ctkdropdownmenu_testing", current_lang.get("main_window_ctkdropdownmenu_testing"), msg1)
    frame.add("main_window_ctkdropdownmenu_settings", current_lang.get("main_window_ctkdropdownmenu_settings"), current_lang.get("main_window_ctkdropdownmenu_settings_look"), msg1)
    frame.add("main_window_ctkdropdownmenu_settings", current_lang.get("main_window_ctkdropdownmenu_settings"), current_lang.get("main_window_ctkdropdownmenu_settings_keybindings"), msg1)
    frame.add("main_window_ctkdropdownmenu_settings", current_lang.get("main_window_ctkdropdownmenu_settings"), current_lang.get("main_window_ctkdropdownmenu_settings_help"), msg1)
    frame.add("main_window_ctkdropdownmenu_settings", current_lang.get("main_window_ctkdropdownmenu_settings"), current_lang.get("main_window_ctkdropdownmenu_settings_about"), msg1)
    frame.pack(fill="x", side="top")
    frame.outside_tracking(app)
