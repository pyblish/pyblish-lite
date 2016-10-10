import os
import sys

import pyblish_lite
from pyblish_lite.vendor.Qt import QtCore

# Remove artificial delay from GUI
os.environ["PYBLISH_DELAY"] = "0"

self = sys.modules[__name__]
self.app = QtCore.QCoreApplication.instance()
self.app = self.app or QtCore.QCoreApplication(sys.argv)
self.module = pyblish_lite
