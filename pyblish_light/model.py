from Qt import QtCore


class Model(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.items = list()

    def __iter__(self):
        """Yield each row of model"""
        for index in range(len(self.items)):
            yield self.createIndex(index, 0)

    def append(self, item):
        """Append item to end of model"""
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())

        self.items.append(item)
        self.endInsertRows()

    def data(self, index, role):
        """Return value of item[`index`] of `role`"""
        item = self.items[index.row()][index.column()]
        return item.get(role)

    def setData(self, index, value, role):
        """Set items[`index`] of `role` to `value`"""
        self.items[index.row()][index.column()][role] = value
        self.dataChanged.emit(index, index, [role])

    def rowCount(self, parent=None):
        return len(self.items)

    def columnCount(self, parent):
        return 2

    def reset(self):
        self.beginResetModel()
        self.items[:] = []
        self.endResetModel()

    def update_with_result(self, result):
        print("Updating with result..")
