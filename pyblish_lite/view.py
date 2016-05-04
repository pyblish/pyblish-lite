from Qt import QtCore, QtWidgets, QtGui

from . import model


class CheckBoxDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.column() == 0:

            rect = QtCore.QRectF(option.rect)
            rect.adjust(8, 8, -8, -8)

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

            painter.save()
            painter.setPen(pen)
            painter.drawPath(path)

            if index.data(model.IsChecked):
                painter.fillPath(path, color)

            painter.restore()

        else:
            return super(CheckBoxDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        widget = QtWidgets.QWidget(parent)
        widget.mousePressEvent = lambda event: (self.setModelData(
            widget, index.model(), index)
            if event.button() & QtCore.Qt.LeftButton
            else None
        )

        return widget

    def sizeHint(self, option, index):
        if index.column() != 0:
            return super(CheckBoxDelegate, self).sizeHint(option, index)

        return QtCore.QSize(10, 10)

    def setModelData(self, editor, mdl, index):
        if index.data(model.IsIdle):
            return

        value = not index.data(model.IsChecked)
        mdl.setData(index, value, model.IsChecked)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class TableView(QtWidgets.QTableView):

    def __init__(self, parent=None):
        super(TableView, self).__init__(parent)

        delegate = CheckBoxDelegate()
        self.setItemDelegate(delegate)

        self.horizontalHeader().setStretchLastSection(True)

        self.setShowGrid(False)

        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.horizontalScrollBar().hide()

        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.NoSelection)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def rowsInserted(self, parent, start, end):
        """Enable editable checkbox for each row"""
        for row in range(start, end + 1):
            index = self.model().createIndex(row, 0)
            self.openPersistentEditor(index)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

        return super(TableView, self).rowsInserted(parent, start, end)
