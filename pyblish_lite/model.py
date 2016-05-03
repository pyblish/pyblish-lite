from Qt import QtCore, __binding__

Label = QtCore.Qt.DisplayRole
IsChecked = QtCore.Qt.UserRole + 0
IsProcessing = QtCore.Qt.UserRole + 1
Actions = QtCore.Qt.UserRole + 2
HasFailed = QtCore.Qt.UserRole + 3
HasSucceeded = QtCore.Qt.UserRole + 4
HasProcessed = QtCore.Qt.UserRole + 6
Id = QtCore.Qt.UserRole + 7


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(TableModel, self).__init__(parent)
        self.items = list()

        # Common schema
        self.schema = {
            IsProcessing: "isProcessing",
            HasProcessed: "hasProcessed",
            HasSucceeded: "hasSucceeded",
            HasFailed: "hasFailed",
            Actions: "actions",
        }

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

    def rowCount(self, parent=None):
        return len(self.items)

    def columnCount(self, parent):
        return 2

    def reset(self):
        self.beginResetModel()
        self.items[:] = []
        self.endResetModel()

    def update_with_result(self, result):
        for record in result["records"]:
            print(record.msg)


class PluginModel(TableModel):
    def __init__(self):
        super(PluginModel, self).__init__()

        self.schema.update({
            Label: "__name__",
            IsChecked: "active",
            Id: "id",
        })

    def append(self, item):
        item.isProcessing = False
        item.hasSucceeded = False
        item.hasFailed = False
        return super(PluginModel, self).append(item)

    def data(self, index, role):
        key = self.schema.get(role)

        if key is None:
            return

        return getattr(self.items[index.row()], key, None)

    def setData(self, index, value, role):
        item = self.items[index.row()]
        key = self.schema.get(role)

        if key is None:
            return

        setattr(item, key, value)

        if __binding__ in ("PyQt4", "PySide"):
            self.dataChanged.emit(index, index)
        else:
            self.dataChanged.emit(index, index, [role])

    def update_with_result(self, result):
        item = result["plugin"]

        index = self.items.index(item)
        index = self.createIndex(index, 0)
        self.setData(index, not result["success"], HasFailed)
        self.setData(index, result["success"], HasSucceeded)
        self.setData(index, True, HasProcessed)
        self.setData(index, False, IsProcessing)
        super(PluginModel, self).update_with_result(result)


class InstanceModel(TableModel):
    def __init__(self):
        super(InstanceModel, self).__init__()

        self.schema.update({
            Label: "label",
            IsChecked: "publish",
        })

    def append(self, item):
        item.data["hasSucceeded"] = False
        item.data["hasFailed"] = False
        item.data["publish"] = item.data.get("publish", True)
        item.data["label"] = item.data.get("label", item.data["name"])
        return super(InstanceModel, self).append(item)

    def data(self, index, role):
        item = self.items[index.row()]
        key = self.schema.get(role)

        if not key:
            return

        return item.data.get(key)

    def setData(self, index, value, role):
        item = self.items[index.row()]
        key = self.schema.get(role)

        if key is None:
            return

        item.data[key] = value

        if __binding__ in ("PyQt4", "PySide"):
            self.dataChanged.emit(index, index)
        else:
            self.dataChanged.emit(index, index, [role])

    def update_with_result(self, result):
        item = result["instance"]

        if item is None:
            return

        index = self.items.index(item)
        index = self.createIndex(index, 0)
        self.setData(index, not result["success"], HasFailed)
        self.setData(index, result["success"], HasSucceeded)
        self.setData(index, True, HasProcessed)
        self.setData(index, False, IsProcessing)
        super(InstanceModel, self).update_with_result(result)
