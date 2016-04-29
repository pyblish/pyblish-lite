from Qt import QtCore, QtWidgets


class CheckBoxDelegate(QtWidgets.QItemDelegate):
    def createEditor(self, parent, option, index):
        return QtWidgets.QCheckBox(parent)

    def sizeHint(self, option, index):
        if index.column() != 0:
            return super(CheckBoxDelegate, self).sizeHint(option, index)

        return QtCore.QSize(15, 15)

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.EditRole)

        if value is not None:
            editor.setCheckState(value)

    def setModelData(self, editor, model, index):
        value = editor.checkState()
        model.setData(index, value, QtCore.Qt.EditRole)

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
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.horizontalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.NoSelection)

    def rowsInserted(self, parent, start, end):
        """Enable editable checkbox for each row"""
        for row in range(start, end + 1):
            index = self.model().createIndex(row, 0)
            self.openPersistentEditor(index)

        return super(TableView, self).rowsInserted(parent, start, end)
