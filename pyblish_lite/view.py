from .vendor.Qt import QtCore, QtWidgets


class Item(QtWidgets.QListView):
    # An item is requesting to be toggled, with optional forced-state
    toggled = QtCore.Signal("QModelIndex", object)

    # An item is requesting details
    inspected = QtCore.Signal("QModelIndex")

    def __init__(self, parent=None):
        super(Item, self).__init__(parent)

        self.horizontalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setVerticalScrollMode(QtWidgets.QListView.ScrollPerPixel)

    def event(self, event):
        if not event.type() == QtCore.QEvent.KeyPress:
            return super(Item, self).event(event)

        elif event.key() == QtCore.Qt.Key_Space:
            for index in self.selectionModel().selectedIndexes():
                self.toggled.emit(index, None)

            return True

        elif event.key() == QtCore.Qt.Key_Backspace:
            for index in self.selectionModel().selectedIndexes():
                self.toggled.emit(index, False)

            return True

        elif event.key() == QtCore.Qt.Key_Return:
            for index in self.selectionModel().selectedIndexes():
                self.toggled.emit(index, True)

            return True

        return super(Item, self).event(event)

    def focusOutEvent(self, event):
        self.selectionModel().clear()

    def leaveEvent(self, event):
        self._inspecting = False
        super(Item, self).leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            self.inspected.emit(index) if index.isValid() else None

        return super(Item, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            indexes = self.selectionModel().selectedIndexes()
            if len(indexes) <= 1 and event.pos().x() < 20:
                for index in indexes:
                    self.toggled.emit(index, None)

        return super(Item, self).mouseReleaseEvent(event)


class LogView(QtWidgets.QListView):

    # An item is requesting details
    inspected = QtCore.Signal("QModelIndex")

    def __init__(self, parent=None):
        super(LogView, self).__init__(parent)

        self.horizontalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QListView.ExtendedSelection)
        self.setVerticalScrollMode(QtWidgets.QListView.ScrollPerPixel)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            self.inspected.emit(index) if index.isValid() else None

        return super(LogView, self).mousePressEvent(event)

    def rowsInserted(self, parent, start, end):
        """Automatically scroll to bottom on each new item added

        Arguments:
            parent (QtCore.QModelIndex): The model itself, since this is a list
            start (int): Start index of item
            end (int): End index of item

        """

        super(LogView, self).rowsInserted(parent, start, end)

        # IMPORTANT: This must be done *after* the superclass to get
        # an accurate value of the delegate's height.
        self.scrollToBottom()


class Details(QtWidgets.QDialog):
    """Popup dialog with detailed information
     _____________________________________
    |                                     |
    | Header                    Timestamp |
    | Subheading                          |
    |                                     |
    |-------------------------------------|
    |                                     |
    | Text                                |
    |_____________________________________|

    """

    def __init__(self, parent=None):
        super(Details, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Popup)
        self.setEnabled(False)
        self.setFixedWidth(100)

        header = QtWidgets.QWidget()

        icon = QtWidgets.QLabel()
        heading = QtWidgets.QLabel()
        subheading = QtWidgets.QLabel()
        timestamp = QtWidgets.QLabel()
        timestamp.setFixedWidth(50)

        layout = QtWidgets.QGridLayout(header)
        layout.addWidget(icon, 0, 0)
        layout.addWidget(heading, 0, 1)
        layout.addWidget(timestamp, 0, 2)
        layout.addWidget(subheading, 1, 1, 1, -1)
        layout.setColumnStretch(1, 1)
        layout.setContentsMargins(5, 5, 5, 5)

        body = QtWidgets.QWidget()

        text = QtWidgets.QLabel()
        text.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(body)
        layout.addWidget(text)
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
            "Icon": icon,
            "Header": header,

            "Heading": heading,
            "Subheading": subheading,
            "Timestamp": timestamp,

            "Body": body,
            "Text": text,
        }

        for name, widget in names.items():
            widget.setObjectName(name)

    def show(self, data):
        # Open before initializing; this allows the widget to properly
        # size itself before filling it with content. The content can
        # then elide itself properly.

        for widget, key in {"Icon": "icon",
                            "Heading": "heading",
                            "Subheading": "subheading",
                            "Timestamp": "timestamp",
                            "Text": "text"}.items():
            widget = self.findChild(QtWidgets.QWidget, widget)
            value = data.get(key, "")

            if key != "text":
                value = widget.fontMetrics().elidedText(value,
                                                        QtCore.Qt.ElideRight,
                                                        widget.width())
            widget.setText(value)
            widget.updateGeometry()

        self.updateGeometry()
        self.setVisible(True)
