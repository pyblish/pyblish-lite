"""Qt models

Description:
    The model contains the original objects from Pyblish, such as
    pyblish.api.Instance and pyblish.api.Plugin. The model then
    provides an interface for reading and writing to those.

GUI data:
    Aside from original data, such as pyblish.api.Plugin.optional,
    the GUI also hosts data internal to itself, such as whether or
    not an item has processed such that it may be colored appropriately
    in the view. This data is prefixed with two underscores (__).

    E.g.

    _has_processed

    This is so that the the GUI-only data doesn't accidentally overwrite
    or cause confusion with existing data in plug-ins and instances.

Roles:
    Data is accessed via standard Qt "roles". You can think of a role
    as the key of a dictionary, except they can only be integers.

"""

from .vendor.Qt import QtCore, __binding__
from .awesome import tags as awesome


# GENERAL

# The original object; Instance or Plugin
Object = QtCore.Qt.UserRole + 0

# Additional data (metadata) about an item
# In the case of instances, this is their data as-is.
# For anyhting else, this is statistics, such as running-time.
Data = QtCore.Qt.UserRole + 16

# The internal .id of any item
Id = QtCore.Qt.UserRole + 1
Type = QtCore.Qt.UserRole + 10

# The display name of an item
Label = QtCore.Qt.DisplayRole + 0
Families = QtCore.Qt.DisplayRole + 1
Icon = QtCore.Qt.DisplayRole + 13

# The item has not been used
IsIdle = QtCore.Qt.UserRole + 2

IsChecked = QtCore.Qt.UserRole + 3
IsOptional = QtCore.Qt.UserRole + 4
IsProcessing = QtCore.Qt.UserRole + 5
HasFailed = QtCore.Qt.UserRole + 6
HasSucceeded = QtCore.Qt.UserRole + 7
HasProcessed = QtCore.Qt.UserRole + 8
Duration = QtCore.Qt.UserRole + 11

# PLUGINS

# Available and context-sensitive actions
Actions = QtCore.Qt.UserRole + 9
ActionIconVisible = QtCore.Qt.UserRole + 13
ActionIdle = QtCore.Qt.UserRole + 15
ActionFailed = QtCore.Qt.UserRole + 17
Docstring = QtCore.Qt.UserRole + 12

# LOG RECORDS

LogThreadName = QtCore.Qt.UserRole + 50
LogName = QtCore.Qt.UserRole + 51
LogFilename = QtCore.Qt.UserRole + 52
LogPath = QtCore.Qt.UserRole + 53
LogLineNumber = QtCore.Qt.UserRole + 54
LogMessage = QtCore.Qt.UserRole + 55
LogMilliseconds = QtCore.Qt.UserRole + 56
LogLevel = QtCore.Qt.UserRole + 61

# EXCEPTIONS

ExcFname = QtCore.Qt.UserRole + 57
ExcLineNumber = QtCore.Qt.UserRole + 58
ExcFunc = QtCore.Qt.UserRole + 59
ExcExc = QtCore.Qt.UserRole + 60


class Abstract(QtCore.QAbstractListModel):
    def __iter__(self):
        """Yield each row of model"""
        for index in range(len(self.items)):
            yield self.createIndex(index, 0)

    def data(self, index, role):
        if role == Object:
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


class Item(Abstract):
    def __init__(self, parent=None):
        super(Item, self).__init__(parent)
        self.items = list()

        self.checkstate = {}

        # Common schema
        self.schema = {
            Label: "label",
            Families: "families",
            Id: "id",
            Actions: "actions",
            IsOptional: "optional",
            Icon: "icon",

            # GUI-only data
            Type: "_type",
            Duration: "_duration",
            IsIdle: "_is_idle",
            IsProcessing: "_is_processing",
            HasProcessed: "_has_processed",
            HasSucceeded: "_has_succeeded",
            HasFailed: "_has_failed",
        }

    def store_checkstate(self):
        self.checkstate.clear()

        for index in self:
            label = index.data(Label)
            families = index.data(Families)
            uid = "{families}.{label}".format(**locals())
            state = index.data(IsChecked)
            self.checkstate[uid] = state

    def restore_checkstate(self):
        for index in self:
            label = index.data(Label)
            families = index.data(Families)

            # Does it have a previous state?
            for uid, state in self.checkstate.items():
                if uid == "{families}.{label}".format(**locals()):
                    self.setData(index, state, IsChecked)
                    break


class Plugin(Item):
    def __init__(self):
        super(Plugin, self).__init__()

        self.schema.update({
            IsChecked: "active",
            Docstring: "__doc__",
            ActionIdle: "_action_idle",
            ActionFailed: "_action_failed",
        })

    def append(self, item):
        item.label = item.label or item.__name__

        # GUI-only data
        item._is_idle = True
        item._is_processing = False
        item._has_processed = False
        item._has_succeeded = False
        item._has_failed = False
        item._type = "plugin"

        item._action_idle = True
        item._action_processing = False
        item._action_succeeded = False
        item._action_failed = False

        return super(Plugin, self).append(item)

    def data(self, index, role):
        item = self.items[index.row()]

        if role == Data:
            return {}

        if role == Icon:
            return awesome.get(getattr(item, "icon", ""))

        if role == ActionIconVisible:

            # Can only run actions on active plug-ins.
            if not item.active:
                return

            actions = list(item.actions)

            # Context specific actions
            for action in actions:
                if action.on == "failed" and not item._has_failed:
                    actions.remove(action)
                if action.on == "succeeded" and not item._has_succeeded:
                    actions.remove(action)
                if action.on == "processed" and not item._has_processed:
                    actions.remove(action)
                if action.on == "notProcessed" and item._has_processed:
                    actions.remove(action)

            if actions:
                return True

            return False

        if role == Actions:

            # Can only run actions on active plug-ins.
            if not item.active:
                return

            actions = list(item.actions)

            # Context specific actions
            for action in actions:
                if action.on == "failed" and not item._has_failed:
                    actions.remove(action)
                if action.on == "succeeded" and not item._has_succeeded:
                    actions.remove(action)
                if action.on == "processed" and not item._has_processed:
                    actions.remove(action)
                if action.on == "notProcessed" and item._has_processed:
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
        value = getattr(item, key, None) if key is not None else None

        if value is None:
            value = super(Plugin, self).data(index, role)

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

    def update_with_result(self, result, action=False):
        item = result["plugin"]

        index = self.items.index(item)
        index = self.createIndex(index, 0)

        self.setData(index, False, IsIdle)
        self.setData(index, False, IsProcessing)
        self.setData(index, True, HasProcessed)
        self.setData(index, result["success"], HasSucceeded)
        self.setData(index, not result["success"], HasFailed)
        super(Plugin, self).update_with_result(result)


class Instance(Item):
    def __init__(self):
        super(Instance, self).__init__()

        self.schema.update({
            IsChecked: "publish",

            # Merge copy of both family and families data members
            Families: "__families__",
        })

    def append(self, item):
        item.data["optional"] = item.data.get("optional", True)
        item.data["publish"] = item.data.get("publish", True)
        item.data["label"] = item.data.get("label", item.data["name"])

        # GUI-only data
        item.data["_type"] = "instance"
        item.data["_has_succeeded"] = False
        item.data["_has_failed"] = False
        item.data["_is_idle"] = True

        # Merge `family` and `families` for backwards compatibility
        item.data["__families__"] = ([item.data["family"]] +
                                     item.data.get("families", []))

        return super(Instance, self).append(item)

    def data(self, index, role):
        item = self.items[index.row()]

        if role == Data:
            return item.data

        if role == Icon:
            return awesome.get(item.data.get("icon"))

        key = self.schema.get(role)
        value = item.data.get(key) if key is not None else None

        if value is None:
            value = super(Instance, self).data(index, role)

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
        super(Instance, self).update_with_result(result)


class Terminal(Abstract):
    def __init__(self, parent=None):
        super(Terminal, self).__init__(parent)
        self.items = list()

        # Common schema
        self.schema = {
            Type: "type",
            Label: "label",

            # Records
            LogThreadName: "threadName",
            LogName: "name",
            LogFilename: "filename",
            LogPath: "pathname",
            LogLineNumber: "lineno",
            LogMessage: "msg",
            LogMilliseconds: "msecs",
            LogLevel: "levelname",

            # Exceptions
            ExcFname: "fname",
            ExcLineNumber: "line_number",
            ExcFunc: "func",
            ExcExc: "exc",
        }

    def data(self, index, role):
        item = self.items[index.row()]

        if role == Data:
            return item

        key = self.schema.get(role)

        if not key:
            return

        value = item.get(key)

        if value is None:
            value = super(Terminal, self).data(index, role)

        return value

    def setData(self, index, value, role):
        item = self.items[index.row()]
        key = self.schema.get(role)

        if key is None:
            return

        item[key] = value

        if __binding__ in ("PyQt4", "PySide"):
            self.dataChanged.emit(index, index)
        else:
            self.dataChanged.emit(index, index, [role])

    def update_with_result(self, result):
        for record in result["records"]:
            self.append({
                "label": str(record.msg),
                "type": "record",

                # Native
                "threadName": record.threadName,
                "name": record.name,
                "filename": record.filename,
                "pathname": record.pathname,
                "lineno": record.lineno,
                "msg": record.msg,
                "msecs": record.msecs,
                "levelname": record.levelname,
            })

        error = result["error"]
        if error is not None:
            fname, line_no, func, exc = error.traceback
            self.append({
                "label": str(error),
                "type": "error",
                "fname": fname,
                "line_number": line_no,
                "func": func,
                "exc": exc,
            })


class ProxyModel(QtCore.QSortFilterProxyModel):
    """A QSortFilterProxyModel with custom exclude and include rules

    Role may be either an integer or string, and each
    role may include multiple values.

    Example:
        >>> # Exclude any item whose role 123 equals "Abc"
        >>> model = ProxyModel(None)
        >>> model.add_exclusion(role=123, value="Abc")

        >>> # Exclude multiple values
        >>> model.add_exclusion(role="name", value="Pontus")
        >>> model.add_exclusion(role="name", value="Richard")

        >>> # Exclude amongst includes
        >>> model.add_inclusion(role="type", value="PluginItem")
        >>> model.add_exclusion(role="name", value="Richard")

    """

    def __init__(self, source, parent=None):
        super(ProxyModel, self).__init__(parent)
        self.setSourceModel(source)

        self.excludes = dict()
        self.includes = dict()

    def item(self, index):
        index = self.index(index, 0, QtCore.QModelIndex())
        index = self.mapToSource(index)
        model = self.sourceModel()
        return model.items[index.row()]

    def add_exclusion(self, role, value):
        """Exclude item if `role` equals `value`

        Attributes:
            role (int, string): Qt role or name to compare `value` to
            value (object): Value to exclude

        """

        self._add_rule(self.excludes, role, value)

    def remove_exclusion(self, role, value=None):
        """Remove exclusion rule

        Arguments:
            role (int, string): Qt role or name to remove
            value (object, optional): Value to remove. If none
                is supplied, the entire role will be removed.

        """

        self._remove_rule(self.excludes, role, value)

    def set_exclusion(self, rules):
        """Set excludes

        Replaces existing excludes with those in `rules`

        Arguments:
            rules (list): Tuples of (role, value)

        """

        self._set_rules(self.excludes, rules)

    def clear_exclusion(self):
        self._clear_group(self.excludes)

    def add_inclusion(self, role, value):
        """Include item if `role` equals `value`

        Attributes:
            role (int): Qt role to compare `value` to
            value (object): Value to exclude

        """

        self._add_rule(self.includes, role, value)

    def remove_inclusion(self, role, value=None):
        """Remove exclusion rule"""
        self._remove_rule(self.includes, role, value)

    def set_inclusion(self, rules):
        self._set_rules(self.includes, rules)

    def clear_inclusion(self):
        self._clear_group(self.includes)

    def _add_rule(self, group, role, value):
        """Implementation detail"""
        if role not in group:
            group[role] = list()

        group[role].append(value)

        self.invalidate()

    def _remove_rule(self, group, role, value=None):
        """Implementation detail"""
        if role not in group:
            return

        if value is None:
            group.pop(role, None)
        else:
            group[role].remove(value)

        self.invalidate()

    def _set_rules(self, group, rules):
        """Implementation detail"""
        group.clear()

        for rule in rules:
            self._add_rule(group, *rule)

        self.invalidate()

    def _clear_group(self, group):
        group.clear()

        self.invalidate()

    # Overridden methods

    def filterAcceptsRow(self, source_row, source_parent):
        """Exclude items in `self.excludes`"""
        model = self.sourceModel()
        item = model.items[source_row]

        key = getattr(item, "filter", None)
        if key is not None:
            regex = self.filterRegExp()
            if regex.pattern():
                match = regex.indexIn(key)
                return False if match == -1 else True

        for role, values in self.includes.items():
            data = getattr(item, role, None)
            if data not in values:
                return False

        for role, values in self.excludes.items():
            data = getattr(item, role, None)
            if data in values:
                return False

        return super(ProxyModel, self).filterAcceptsRow(
            source_row, source_parent)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return super(ProxyModel, self).rowCount(parent)
