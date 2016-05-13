import os
import sys

import pyblish_lite
from Qt import QtWidgets

# Remove artificial delay from GUI
os.environ["PYBLISH_DELAY"] = "0"

self = sys.modules[__name__]
self.app = QtWidgets.QApplication.instance()
self.app = self.app or QtWidgets.QApplication(sys.argv)
self.module = pyblish_lite
