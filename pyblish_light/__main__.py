import sys
import contextlib

from Qt import QtWidgets, QtGui
from .app import Window

import pyblish.api


class MyCollector(pyblish.api.ContextPlugin):
    order = pyblish.api.CollectorOrder

    def process(self, context):
        context.create_instance("MyInstance 1", families=["myFamily"])
        context.create_instance("MyInstance 2", families=["myFamily 2"])
        context.create_instance(
            "MyInstance 3",
            families=["myFamily 2"],
            publish=False
        )


class MyValidator(pyblish.api.InstancePlugin):
    order = pyblish.api.ValidatorOrder
    active = False

    def process(self, instance):
        self.log.info("Validating: %s" % instance)


class MyExtractor(pyblish.api.InstancePlugin):
    order = pyblish.api.ExtractorOrder
    families = ["myFamily"]

    def process(self, instance):
        self.log.info("Extracting: %s" % instance)


pyblish.api.register_plugin(MyCollector)
pyblish.api.register_plugin(MyValidator)
pyblish.api.register_plugin(MyExtractor)


@contextlib.contextmanager
def application():
    if QtWidgets.qApp is None:
        app = QtWidgets.QApplication(sys.argv)
        yield app
        app.exec_()
    else:
        yield QtWidgets.qApp


def install_fonts():
    fontdir = os.path.join(os.getcwd(), "font", "opensans")

    database = QtGui.QFontDatabase()
    for font in ("OpenSans-Regular.ttf",
                 "OpenSans-SemiBold.ttf"):
        database.addApplicationFont(
            os.path.join(fontdir, font))


if __name__ == '__main__':
    import os

    os.chdir(os.path.dirname(__file__))

    with open("app.css") as f:
        css = f.read()

    with application():
        install_fonts()

        window = Window()
        window.resize(400, 600)
        window.setStyleSheet(css)
        window.show()

        window.prepare_reset()
