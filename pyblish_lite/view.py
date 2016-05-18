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

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            self.inspected.emit(index, True)

        return super(Item, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            indexes = self.selectionModel().selectedIndexes()
            if len(indexes) <= 1:
                for index in indexes:
                    self.toggled.emit(index, None)

        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            self.inspected.emit(index, False)

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

        index = self.model().createIndex(end, 0)
        self.scrollTo(index)

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
        layout.addWidget(label, 0, 0, 0)
        layout.addWidget(families, 1, 0, 0)
        layout.addWidget(spacer, 0, 1, 1)
        layout.addWidget(duration, 0, 2, 0)

        body = QtWidgets.QWidget()
        view = LogView()

        layout = QtWidgets.QVBoxLayout(body)
        layout.addWidget(view)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(body)

        names = {
            # Main
            "Header": header,
            "Body": body,

            "Heading": label,
            "Subheading": families,
            "Duration": duration,
            "View": view
        }

        for name, widget in names.items():
            widget.setObjectName(name)

        self.view = view

    def init(self, data):
        heading = self.findChild(QtWidgets.QWidget, "Heading")
        subheading = self.findChild(QtWidgets.QWidget, "Subheading")
        duration = self.findChild(QtWidgets.QWidget, "Duration")

        heading.setText(data["heading"])
        subheading.setText(data["subheading"])
        duration.setText(data["duration"])

    def setModel(self, model):
        self.view.setModel(model)

    def model(self):
        return self.view.model()
