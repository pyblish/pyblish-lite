import os
import sys
import contextlib

from .vendor.Qt import QtWidgets, QtGui
from . import control, util, window, compat, settings

self = sys.modules[__name__]

# Maintain reference to currently opened window
self._window = None


@contextlib.contextmanager
def application():
    app = QtWidgets.QApplication.instance()

    if not app:
        print("Starting new QApplication..")
        app = QtWidgets.QApplication(sys.argv)
        yield app
        app.exec_()
    else:
        print("Using existing QApplication..")
        yield app


def install_fonts():
    database = QtGui.QFontDatabase()

    for font in (os.path.join("opensans", "OpenSans-Regular.ttf"),
                 os.path.join("opensans", "OpenSans-Semibold.ttf"),
                 os.path.join("fontawesome", "fontawesome-webfont.ttf")):
        path = util.get_asset("font", font)

        # TODO(marcus): Check if they are already installed first.
        # In hosts, this will be called each time the GUI is shown,
        # potentially installing a font each time.
        if database.addApplicationFont(path) < 0:
            sys.stderr.write("Could not install %s\n" % path)
        else:
            sys.stdout.write("Installed %s\n" % font)


def on_destroyed():
    """Remove internal reference to window on window destroyed"""
    self._window = None


def show(parent=None):
    with open(util.get_asset("app.css")) as f:
        css = f.read()

        # Make relative paths absolute
        root = util.get_asset("").replace("\\", "/")
        css = css.replace("url(\"", "url(\"%s" % root)

    with application():
        compat.init()

        install_fonts()

        ctrl = control.Controller()

        if self._window is None:
            self._window = window.Window(ctrl, parent)
            self._window.destroyed.connect(on_destroyed)

        self._window.show()
        self._window.activateWindow()
        self._window.resize(430, 600)
        self._window.setWindowTitle(settings.WindowTitle)

        font = self._window.font()
        font.setFamily("Open Sans")
        font.setPointSize(8)
        font.setWeight(400)

        self._window.setFont(font)
        self._window.setStyleSheet(css)

        self._window.reset()

        return self._window
