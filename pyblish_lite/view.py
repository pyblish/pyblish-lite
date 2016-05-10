from Qt import QtCore, QtWidgets, QtGui

from . import model


class CheckBoxDelegate(QtWidgets.QStyledItemDelegate):
    toggled = QtCore.Signal("QModelIndex")

    def paint(self, painter, option, index):
        """Paint checkbox and text
         _
        |_|  My label

        """

        rect = QtCore.QRectF(option.rect)
        rect.setWidth(rect.height())
        rect.adjust(4, 4, -4, -4)

        path = QtGui.QPainterPath()
        path.addRect(rect)

        color = QtCore.Qt.white

        if index.data(model.IsProcessing) is True:
            color = QtCore.Qt.green

        elif index.data(model.HasFailed) is True:
            color = QtCore.Qt.red

        elif index.data(model.HasSucceeded) is True:
            color = QtCore.Qt.green

        pen = QtGui.QPen(color, 1)
        font = QtWidgets.QApplication.instance().font()
        metrics = painter.fontMetrics()

        rect = option.rect.adjusted(rect.width() + 10, 2, 0, -2)
        label = index.data(model.Label)
        label = metrics.elidedText(label, QtCore.Qt.ElideRight, rect.width())

        # Maintan reference to state, so we can restore it once we're done
        painter.save()

        # Draw label
        painter.setFont(font)
        painter.drawText(rect, label)

        # Draw checkbox
        painter.setPen(pen)
        painter.drawPath(path)

        if index.data(model.IsChecked):
            painter.fillPath(path, color)

        # Ok, we're done, tidy up.
        painter.restore()

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), 20)

    def createEditor(self, parent, option, index):
        """Handle events, such as mousePressEvent"""
        widget = QtWidgets.QWidget(parent)

        # At the moment, clicking anywhere on the item triggers a toggle
        # TODO(marcus): Distinguish when a user is pressing on a potential
        # icon other than the main label or checkbox.
        widget.mouseReleaseEvent = lambda event: (
            self.toggled.emit(index)
            if event.button() & QtCore.Qt.LeftButton
            else None
        )

        return widget

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
        return super(CheckBoxDelegate, self).updateEditorGeometry(
            editor, option, index)


class ItemView(QtWidgets.QListView):

    def __init__(self, parent=None):
        super(ItemView, self).__init__(parent)

        self.verticalScrollBar().hide()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def rowsInserted(self, parent, start, end):
        """Enable editable checkbox for each row"""
        for row in range(start, end + 1):
            index = self.model().createIndex(row, 0)
            self.openPersistentEditor(index)

        return super(ItemView, self).rowsInserted(parent, start, end)
