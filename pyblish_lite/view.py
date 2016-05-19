from Qt import QtCore, QtWidgets


class Item(QtWidgets.QListView):
    # An item is requesting to be toggled, with optional forced-state
    toggled = QtCore.Signal("QModelIndex", object)

    # An item is requesting details, True means show, False means hide
    inspected = QtCore.Signal("QModelIndex", bool)

    def __init__(self, parent=None):
        super(Item, self).__init__(parent)

        self.verticalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self._inspecting = False

    def event(self, event):
        if not event.type() == QtCore.QEvent.KeyPress:
            return super(Item, self).event(event)

        if event.key() == QtCore.Qt.Key_Space:
            for index in self.selectionModel().selectedIndexes():
                self.toggled.emit(index, None)

            return True

        if event.key() == QtCore.Qt.Key_Backspace:
            for index in self.selectionModel().selectedIndexes():
                self.toggled.emit(index, False)

            return True

        if event.key() == QtCore.Qt.Key_Return:
            for index in self.selectionModel().selectedIndexes():
                self.toggled.emit(index, True)

            return True

        return super(Item, self).event(event)

    def focusOutEvent(self, event):
        self.selectionModel().clear()

    def leaveEvent(self, event):
        self._inspecting = False
        super(Item, self).leaveEvent(event)

    def mouseMoveEvent(self, event):
        if self._inspecting:
            index = self.indexAt(event.pos())
            self.inspected.emit(index, True) if index.isValid() else None

        return super(Item, self).mouseMoveEvent(event)

    def mousePressEvent(self, event):
        self._inspecting = event.button() == QtCore.Qt.MidButton
        return super(Item, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            indexes = self.selectionModel().selectedIndexes()
            if len(indexes) <= 1:
                for index in indexes:
                    self.toggled.emit(index, None)

        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            self.inspected.emit(index, False) if index.isValid() else None
            self._inspecting = False

        return super(Item, self).mouseReleaseEvent(event)


class LogView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(LogView, self).__init__(parent)

        self.verticalScrollBar().hide()
        self.horizontalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def rowsInserted(self, parent, start, end):
        """Enable editable checkbox for each row

        Arguments:
            parent (QtCore.QModelIndex): The model itself, since this is a list
            start (int): Start index of item
            end (int): End index of item

        """

        self.scrollToBottom()

        return super(LogView, self).rowsInserted(parent, start, end)


class Details(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Details, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.ToolTip)

        header = QtWidgets.QWidget()

        label = QtWidgets.QLabel("My Instance")
        families = QtWidgets.QLabel("default, cfx, simRig")
        duration = QtWidgets.QLabel("255 ms")
        spacer = QtWidgets.QWidget()

        layout = QtWidgets.QGridLayout(header)
        layout.addWidget(label, 0, 0)
        layout.addWidget(families, 1, 0)
        layout.addWidget(spacer, 0, 1)
        layout.addWidget(duration, 0, 2)
        layout.setColumnStretch(1, 1)
        layout.setContentsMargins(5, 5, 5, 5)

        body = QtWidgets.QWidget()

        docstring = QtWidgets.QLabel("Hello World")

        layout = QtWidgets.QVBoxLayout(body)
        layout.addWidget(docstring)
        layout.setContentsMargins(5, 5, 5, 5)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for widget in (header,
                       body):
            widget.setAttribute(QtCore.Qt.WA_StyledBackground)

        names = {
            # Main
            "Header": header,

            "Heading": label,
            "Subheading": families,
            "Duration": duration,

            "Body": body,
            "Docstring": docstring,
        }

        for name, widget in names.items():
            widget.setObjectName(name)

    def init(self, data):
        for widget, key in {"Heading": "label",
                            "Subheading": "families",
                            "Duration": "duration",
                            "Docstring": "docstring"}.items():
            widget = self.findChild(QtWidgets.QWidget, widget)
            value = data[key]

            value = widget.fontMetrics().elidedText(value,
                                                    QtCore.Qt.ElideRight,
                                                    widget.width())
            widget.setText(value)

    def leaveEvent(self, event):
        self.hide()
        return super(Details, self).leaveEvent(event)
