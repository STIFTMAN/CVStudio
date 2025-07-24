import src

src.gui.utils.config_loader.load()
src.gui.utils.lang_loader.load()
src.gui.layout.main_window.build()
src.gui.state.root.app.mainloop()
