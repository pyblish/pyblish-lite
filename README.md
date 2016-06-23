### Pyblish Lite

[![Build Status](https://travis-ci.org/pyblish/pyblish-lite.svg?branch=master)](https://travis-ci.org/pyblish/pyblish-lite) [![Coverage Status](https://coveralls.io/repos/github/pyblish/pyblish-lite/badge.svg?branch=master)](https://coveralls.io/github/pyblish/pyblish-lite?branch=master)

A lightweight alternative to [pyblish-qml](https://github.com/pyblish/pyblish-qml).

![untitled](https://cloud.githubusercontent.com/assets/2152766/15649651/0785cdc2-266b-11e6-81aa-182e55234854.gif)

**Supports**

Python 2.6+ and Python 3.x+

- PySide
- PySide2
- PyQt4
- PyQt5

<br>
<br>
<br>

### Installation

You can install via pip, or clone manually.

```bash
$ pip install pyblish-lite
$ python -m pyblish_lite --debug  # Test install
```

Requires [pyblish-base](https://github.com/pyblish/pyblish-base).

<br>
<br>
<br>

### Usage

Pyblish Lite runs both standalone and from a host and requires either PySide of PyQt bindings to be readily available.

- [Terminal](#terminal)
- [Python](#python)
- [Maya](#maya)
- [Nuke](#nuke)
- [Mari](#mari)
- [Houdini](#houdini)

##### Terminal

```bash
$ python -m pyblish_lite
```

##### Python

```python
import pyblish_lite
pyblish_lite.show()
```

##### Maya

```python
import pyblish.api
import pyblish_lite

pyblish.api.register_host("maya")

window = pyblish_lite.show()
```

##### Nuke

```python
import pyblish.api
import pyblish_lite

pyblish.api.register_host("nuke")

window = pyblish_lite.show()
```

##### Mari

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

##### Houdini

ATTENTION: This can't be run from the Houdini Python terminal, it'll crash the process.

```python
import pyblish.api
import pyblish_lite

pyblish.api.register_host("houdini")

window = pyblish_lite.show()
```
