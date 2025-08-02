import src

src.gui.utils.config_loader.load()
src.gui.utils.lang_loader.load()
src.gui.utils.style_loader.load()
src.gui.utils.keybindings_loader.load()
src.gui.utils.project_loader.load()
src.gui.state.app.app.build()
src.gui.state.app.app.mainloop()
