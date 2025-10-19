from pathlib import Path
import src.gui.utils.logger as log
from src.gui.state.error import Info
import src.gui.utils.config_loader
import src.gui.utils.lang_loader
import src.gui.utils.style_loader
import src.gui.utils.keybindings_loader
import src.gui.utils.project_loader
import src.gui.state.app


def main():
    log.log.reset()
    log.log.write(text=Info.PRELOADING_CONFIG.value, tag="INFO", modulename=Path(__file__).stem)
    src.gui.utils.config_loader.load()
    log.log.write(text=Info.PRELOADING_LANG.value, tag="INFO", modulename=Path(__file__).stem)
    src.gui.utils.lang_loader.load()
    log.log.write(text=Info.PRELOADING_STYLE.value, tag="INFO", modulename=Path(__file__).stem)
    src.gui.utils.style_loader.load()
    log.log.write(text=Info.PRELOADING_KEYBINDING.value, tag="INFO", modulename=Path(__file__).stem)
    src.gui.utils.keybindings_loader.load()
    log.log.write(text=Info.PRELOADING_PROJECT.value, tag="INFO", modulename=Path(__file__).stem)
    src.gui.utils.project_loader.load()
    log.log.write(text=Info.BUILDING_MAIN.value, tag="INFO", modulename=Path(__file__).stem)
    src.gui.state.app.app.build()
    log.log.write(text=Info.INIT_DONE.value, tag="INFO", modulename=Path(__file__).stem)
    src.gui.state.app.app.mainloop()
    log.log.write(text=Info.CLOSE_WINDOW.value, tag="INFO", modulename=Path(__file__).stem)


if __name__ == "__main__":
    main()
