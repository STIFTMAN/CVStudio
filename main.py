import src.gui.utils.config_loader
import src.gui.utils.lang_loader
import src.gui.utils.style_loader
import src.gui.utils.keybindings_loader
import src.gui.utils.project_loader
import src.gui.state.app


def main():
    src.gui.utils.config_loader.load()
    src.gui.utils.lang_loader.load()
    src.gui.utils.style_loader.load()
    src.gui.utils.keybindings_loader.load()
    src.gui.utils.project_loader.load()
    src.gui.state.app.app.build()
    src.gui.state.app.app.mainloop()


if __name__ == "__main__":
    main()
