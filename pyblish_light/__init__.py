import sys

# Support Qt 4 and 5, PyQt and PySide
try:
    import PyQt5.Qt
    sys.modules["Qt"] = PyQt5
    PyQt5.Signal = PyQt5.pyqtSignal
    PyQt5.Slot = PyQt5.pyqtSlot
    PyQt5.Property = PyQt5.pyqtProperty

except ImportError:
    import PyQt4.Qt
    sys.modules["Qt"] = PyQt4
    PyQt5.Signal = PyQt5.pyqtSignal
    PyQt5.Slot = PyQt5.pyqtSlot
    PyQt5.Property = PyQt5.pyqtProperty

except ImportError:
    import PySide2
    sys.modules["Qt"] = PySide2

except ImportError:
    import PySide
    PySide.QtWidgets = PySide.QtGui
    sys.modules["Qt"] = PySide

except:
    sys.stderr.write("pyblish-light: Could not find "
                     "appropriate bindings for Qt\n")
