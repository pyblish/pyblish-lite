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

**Maya**

```python
from PySide import QtGui

import pyblish.api
import pyblish_lite

pyblish.api.register_host("maya")

parent = {o.objectName(): o for o in QtGui.qApp.topLevelWidgets()}["MayaWindow"]
window = pyblish_lite.show(parent)
```

**Nuke**

```python
import pyblish.api
import pyblish_lite

pyblish.api.register_host("nuke")

window = pyblish_lite.show()
```

**Mari**

```python
from PySide import QtGui

import mari
import pyblish.api
import pyblish_lite

pyblish.api.register_host("mari")

mari.app.activateMainWindow()
parent = QtGui.qApp.activeWindow()

window = pyblish_lite.show(parent)
```

**Houdini 15**

ATTENTION: This must be started from a shelf button.

```python
import hou
import pyblish.api
import pyblish_lite

pyblish.api.register_host("houdini")

parent = hou.ui.mainQtWindow()
window = pyblish_lite.show(parent)
```

Houdini < 15.0 doesn't have the call to `mainQtWindow` but should work well without it, unless you find a way to grab the window yourself.
