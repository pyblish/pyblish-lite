import os
import sys

# Remove artificial delay from GUI
os.environ["PYBLISH_DELAY"] = "0"

path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, path)

from pyblish_lite import compat
compat.init()

from Qt import QtWidgets

self = sys.modules[__name__]
self.app = QtWidgets.qApp.instance()
self.app = self.app or QtWidgets.QApplication(sys.argv)
