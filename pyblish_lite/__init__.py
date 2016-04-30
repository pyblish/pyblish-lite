import sys


VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_PATCH = 0

version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
version = '%i.%i.%i' % version_info
__version__ = version


def load_pyqt5():
    import PyQt5.Qt
    sys.modules["Qt"] = PyQt5
    PyQt5.QtCore.Signal = PyQt5.QtCore.pyqtSignal
    PyQt5.QtCore.Slot = PyQt5.QtCore.pyqtSlot
    PyQt5.QtCore.Property = PyQt5.QtCore.pyqtProperty
    print("Loaded PyQt5")


def load_pyqt4():
    import PyQt4.Qt
    sys.modules["Qt"] = PyQt4
    PyQt4.QtWidgets = PyQt4.QtGui
    PyQt4.QtCore.Signal = PyQt4.QtCore.pyqtSignal
    PyQt4.QtCore.Slot = PyQt4.QtCore.pyqtSlot
    PyQt4.QtCore.Property = PyQt4.QtCore.pyqtProperty
    print("Loaded PyQt4")


def load_pyside2():
    import PySide2
    sys.modules["Qt"] = PySide2
    print("Loaded PySide2")


def load_pyside():
    import PySide
    from PySide import QtGui
    PySide.QtWidgets = QtGui
    sys.modules["Qt"] = PySide
    print("Loaded PySide")


# Support Qt 4 and 5, PyQt and PySide
try:
    load_pyside()
except ImportError:
    try:
        load_pyqt4()
    except ImportError:
        try:
            load_pyside2()
        except ImportError:
            try:
                load_pyqt5()
            except:
                sys.stderr.write("pyblish-lite: Could not find "
                                 "appropriate bindings for Qt\n")

from .app import show

__all__ = [
    'show',
    'version',
    'version_info',
    '__version__'
]
