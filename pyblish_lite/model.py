from Qt import QtCore, __binding__


# GENERAL

# The original object; Context, Instance or Plugin
Item = QtCore.Qt.UserRole + 0

# The internal .id of any item
Id = QtCore.Qt.UserRole + 1

# The display name of an item
Label = QtCore.Qt.DisplayRole

# The item has not been used
IsIdle = QtCore.Qt.UserRole + 2

IsChecked = QtCore.Qt.UserRole + 3
IsOptional = QtCore.Qt.UserRole + 4
IsProcessing = QtCore.Qt.UserRole + 5
HasFailed = QtCore.Qt.UserRole + 6
HasSucceeded = QtCore.Qt.UserRole + 7
HasProcessed = QtCore.Qt.UserRole + 8

# PLUGINS

# Available and context-sensitive actions
Actions = QtCore.Qt.UserRole + 9

# LOG RECORDS

LogThreadName = QtCore.Qt.UserRole + 50
LogName = QtCore.Qt.UserRole + 51
LogFilename = QtCore.Qt.UserRole + 52
LogPath = QtCore.Qt.UserRole + 53
LogLineNumber = QtCore.Qt.UserRole + 54
LogMessage = QtCore.Qt.UserRole + 55
LogMilliseconds = QtCore.Qt.UserRole + 56

# EXCEPTIONS

ExcFname = QtCore.Qt.UserRole + 57
ExcLineNumber = QtCore.Qt.UserRole + 58
ExcFunc = QtCore.Qt.UserRole + 59
ExcExc = QtCore.Qt.UserRole + 60


class AbstractModel(QtCore.QAbstractListModel):
    def __iter__(self):
        """Yield each row of model"""
        for index in range(len(self.items)):
            yield self.createIndex(index, 0)

    def data(self, index, role):
        if role == Item:
            return self.items[index.row()]

    def append(self, item):
        """Append item to end of model"""
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rowCount(),
                             self.rowCount())

        self.items.append(item)
        self.endInsertRows()

    def rowCount(self, parent=None):
        return len(self.items)

    def reset(self):
        self.beginResetModel()
        self.items[:] = []
        self.endResetModel()

    def update_with_result(self, result):
        pass


class ItemModel(AbstractModel):
    def __init__(self, parent=None):
        super(ItemModel, self).__init__(parent)
        self.items = list()

        # Common schema
        self.schema = {
            Label: "label",
            Id: "id",
            IsIdle: "is_idle",
            IsProcessing: "is_processing",
            HasProcessed: "has_processed",
            HasSucceeded: "has_succeeded",
            HasFailed: "has_failed",
            Actions: "actions",
            IsOptional: "optional"
        }


class PluginModel(ItemModel):
    def __init__(self):
        super(PluginModel, self).__init__()

        self.schema.update({
            IsChecked: "active",
        })

    def append(self, item):
        item.is_idle = True
        item.is_processing = False
        item.has_processed = False
        item.has_succeeded = False
        item.has_failed = False
        item.label = item.label or item.__name__
        return super(PluginModel, self).append(item)

    def data(self, index, role):
        item = self.items[index.row()]
        key = self.schema.get(role)

        if key is None:
            return

        if role == Actions:
            actions = list(item.actions)

            # Context specific actions
            for action in actions:
                if action.on == "failed" and not item.has_failed:
                    actions.remove(action)
                if action.on == "succeeded" and not item.has_succeeded:
                    actions.remove(action)
                if action.on == "processed" and not item.has_processed:
                    actions.remove(action)
                if action.on == "notProcessed" and item.has_processed:
                    actions.remove(action)

            # Discard empty groups
            i = 0
            try:
                action = actions[i]
            except IndexError:
                pass
            else:
                while action:
                    try:
                        action = actions[i]
                    except IndexError:
                        break

                    isempty = False

                    if action.__type__ == "category":
                        try:
                            next_ = actions[i + 1]
                            if next_.__type__ != "action":
                                isempty = True
                        except IndexError:
                            isempty = True

                        if isempty:
                            actions.pop(i)

                    i += 1

            return actions

        key = self.schema.get(role)

        if key is None:
            return

        value = getattr(item, key, None)

        if value is None:
            value = super(PluginModel, self).data(index, role)

        return value

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
        self.setData(index, False, IsIdle)
        self.setData(index, False, IsProcessing)
        self.setData(index, True, HasProcessed)
        self.setData(index, result["success"], HasSucceeded)
        self.setData(index, not result["success"], HasFailed)
        super(PluginModel, self).update_with_result(result)


class InstanceModel(ItemModel):
    def __init__(self):
        super(InstanceModel, self).__init__()

        self.schema.update({
            IsChecked: "publish",
        })

    def append(self, item):
        item.data["has_succeeded"] = False
        item.data["has_failed"] = False
        item.data["is_idle"] = True
        item.data["optional"] = item.data.get("optional", True)
        item.data["publish"] = item.data.get("publish", True)
        item.data["label"] = item.data.get("label", item.data["name"])
        return super(InstanceModel, self).append(item)

    def data(self, index, role):
        item = self.items[index.row()]
        key = self.schema.get(role)

        if not key:
            return

        value = item.data.get(key)

        if value is None:
            value = super(InstanceModel, self).data(index, role)

        return value

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
        self.setData(index, False, IsIdle)
        self.setData(index, False, IsProcessing)
        self.setData(index, True, HasProcessed)
        self.setData(index, result["success"], HasSucceeded)
        self.setData(index, not result["success"], HasFailed)
        super(InstanceModel, self).update_with_result(result)


class LogModel(AbstractModel):
    def __init__(self, parent=None):
        super(LogModel, self).__init__(parent)
        self.items = list()

        # Common schema
        self.schema = {
            Label: "msg",

            # Records
            LogThreadName: "threadName",
            LogName: "name",
            LogFilename: "filename",
            LogPath: "pathname",
            LogLineNumber: "lineno",
            LogMessage: "msg",
            LogMilliseconds: "msecs",

            # Exceptions
            ExcFname: "fname",
            ExcLineNumber: "line_number",
            ExcFunc: "func",
            ExcExc: "exc",
        }

    def data(self, index, role):
        item = self.items[index.row()]
        key = self.schema.get(role)

        if not key:
            return

        value = item.get(key)

        if value is None:
            value = super(LogModel, self).data(index, role)

        return value

    def update_with_result(self, result):
        for record in result["records"]:
            # print("Appending %s" % record.__dict__)
            self.append(record.__dict__)
