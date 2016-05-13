from Qt import QtCore, QtWidgets


class Item(QtWidgets.QListView):
    toggled = QtCore.Signal("QModelIndex", object)

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

        return super(Item, self).keyPressEvent(event)

    def focusOutEvent(self, event):
        self.selectionModel().clear()

    def mouseReleaseEvent(self, event):
        indexes = self.selectionModel().selectedIndexes()
        if len(indexes) <= 1:
            for index in indexes:
                self.toggled.emit(index, None)

        return super(Item, self).mouseReleaseEvent(event)


class LogView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(LogView, self).__init__(parent)

        self.verticalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
