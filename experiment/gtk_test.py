# gtk_test.py

import sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib

def gtk_window():
    QUIT = False

    def quit_(window):
        nonlocal QUIT
        QUIT = True

    class MainWindow(Gtk.Window):
        def __init__(self):
            super().__init__()

    window = MainWindow()
    window.connect("close-request", quit_)
    window.show()

    loop = GLib.MainContext().default()
    while not QUIT:
        loop.iteration(True)

def gtk_applicationwindow():
    class MainWindow(Gtk.ApplicationWindow):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_default_size(800, 600)
            self.app_ = self.get_application()

    class MyApp(Gtk.Application):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def do_activate(self):
            active_window = self.props.active_window
            if active_window:
                active_window.present()
            else:
                self.win = MainWindow(application=self)
                self.win.present()

    app = MyApp(application_id="com.github.yucefsourani.myapplicationexample",
                flags=Gio.ApplicationFlags.FLAGS_NONE)
    app.run(sys.argv)


if __name__ == "__main__":
    #gtk_window()
    gtk_applicationwindow()
