import os
import sys
import contextlib

from .vendor.Qt import QtWidgets, QtGui
from . import control, util, window, compat


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

        win = window.Window(ctrl, parent)
        win.resize(430, 600)
        win.show()

        font = win.font()
        font.setFamily("Open Sans")
        font.setPointSize(8)
        font.setWeight(400)

        win.setFont(font)
        win.setStyleSheet(css)

        win.reset()

        return win
