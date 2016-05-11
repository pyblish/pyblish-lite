import os
import sys
import contextlib

from Qt import QtWidgets, QtGui

from . import control


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
    fontdir = os.path.join(os.getcwd(), "font", "opensans")

    database = QtGui.QFontDatabase()
    for font in ("OpenSans-Regular.ttf",
                 "OpenSans-Semibold.ttf"):
        database.addApplicationFont(
            os.path.join(fontdir, font))


def show(parent=None):
    os.chdir(os.path.dirname(__file__))

    with open("app.css") as f:
        css = f.read()

    with application():
        install_fonts()

        window = control.Window(parent)
        window.resize(400, 600)
        window.show()

        font = window.font()
        font.setFamily("Open Sans")
        font.setPointSize(8)
        font.setWeight(400)

        window.setFont(font)
        window.setStyleSheet(css)

        window.prepare_reset()

        return window
