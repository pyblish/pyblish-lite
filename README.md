### Pyblish Lite

A lightweight alternative to [pyblish-qml](https://github.com/pyblish/pyblish-qml).

![untitled](https://cloud.githubusercontent.com/assets/2152766/14935732/054d938c-0ed3-11e6-9468-a3935a0e5184.gif)

**Supports**

Python 2.6+ and Python 3.x+

- PySide
- PySide2
- PyQt4
- PyQt5

<br>
<br>
<br>

### Usage

Pyblish Lite runs both standalone and from a host and requires either PySide of PyQt bindings to be readily available.

**Terminal**

```bash
$ python -m pyblish_lite
```

**Python**

```python
import pyblish_lite
pyblish_lite.show()
```

**Audodesk Maya**

```python
from PySide import QtGui
import pyblish_lite

parent = {o.objectName(): o for o in QtGui.qApp.topLevelWidgets()}["MayaWindow"]
window = pyblish_lite.show(parent)
```

<br>
<br>
<br>

### Todo

- Reflect changes in GUI when publishing
- Terminal in which log records are shown
