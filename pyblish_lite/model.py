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
from __future__ import unicode_literals
import traceback

import pyblish

from . import settings, util
from .awesome import tags as awesome
from .vendor.Qt import QtCore, QtGui, __binding__
from .vendor.six import text_type

try:
    from pypeapp import config
    get_presets = config.get_presets
except Exception:
    get_presets = dict

# GENERAL

# The original object; Instance or Plugin
Object = QtCore.Qt.UserRole + 0

# The internal .id of any item
Id = QtCore.Qt.UserRole + 1
Type = QtCore.Qt.UserRole + 2

# Additional data (metadata) about an item
# In the case of instances, this is their data as-is.
# For anyhting else, this is statistics, such as running-time.
Data = QtCore.Qt.UserRole + 3

# The display name of an item
Label = QtCore.Qt.UserRole + 4
Name = QtCore.Qt.UserRole + 5
Families = QtCore.Qt.UserRole + 6
Icon = QtCore.Qt.UserRole + 7

Duration = QtCore.Qt.UserRole + 8
Order = QtCore.Qt.UserRole + 9
GroupObject = QtCore.Qt.UserRole + 10

IntentItemValue = QtCore.Qt.UserRole + 11

# The item has not been used
IsIdle = QtCore.Qt.UserRole + 15
IsProcessing = QtCore.Qt.UserRole + 16
HasProcessed = QtCore.Qt.UserRole + 17
HasSucceeded = QtCore.Qt.UserRole + 18
HasFailed = QtCore.Qt.UserRole + 19
IsOptional = QtCore.Qt.UserRole + 20
IsChecked = QtCore.Qt.UserRole + 21

HasWarning = QtCore.Qt.UserRole + 22

# PLUGINS
HasCompatible = QtCore.Qt.UserRole + 30
Docstring = QtCore.Qt.UserRole + 31
PathModule = QtCore.Qt.UserRole + 32

# Available and context-sensitive actions
Actions = QtCore.Qt.UserRole + 33
ActionIconVisible = QtCore.Qt.UserRole + 34
ActionIdle = QtCore.Qt.UserRole + 35
ActionFailed = QtCore.Qt.UserRole + 36


LogRecord = QtCore.Qt.UserRole + 40
ErrorRecord = QtCore.Qt.UserRole + 41

# LOG RECORDS
LogThreadName = QtCore.Qt.UserRole + 42
LogName = QtCore.Qt.UserRole + 43
LogFilename = QtCore.Qt.UserRole + 44
LogPath = QtCore.Qt.UserRole + 45
LogLineNumber = QtCore.Qt.UserRole + 46
LogMessage = QtCore.Qt.UserRole + 47
LogMilliseconds = QtCore.Qt.UserRole + 48
LogLevel = QtCore.Qt.UserRole + 49
LogSize = QtCore.Qt.UserRole + 50
# EXCEPTIONS
# Duplicates with LogFilename and LogLineNumber
# ExcFname = QtCore.Qt.UserRole + 57
# ExcLineNumber = QtCore.Qt.UserRole + 58
ExcFunc = QtCore.Qt.UserRole + 51
ExcTraceback = QtCore.Qt.UserRole + 52


class IntentModel(QtGui.QStandardItemModel):
    """Model for QComboBox with intents.

    It is expected that one inserted item is dictionary.
    Key represents #Label and Value represent #Value.

    Example:
    {
        "Testing": "test",
        "Publishing": "publish"
    }

    First and default value is {"< Not Set >": None}
    """

    default_item = {"< Not Set >": None}

    def __init__(self, parent=None):
        super(IntentModel, self).__init__(parent)
        self._item_count = 0

    @property
    def has_items(self):
        return self._item_count > 0

    def reset(self):
        self.clear()
        self._item_count = 0

        intents_preset = (
            get_presets()
            .get("tools", {})
            .get("pyblish", {})
            .get("ui", {})
            .get("intents", {})
        )
        items = intents_preset.get("items", {})
        if not items:
            return

        default = intents_preset.get("default", True)
        if default:
            self.add_items(self.default_item)
        self.add_items(items)

    def add_items(self, items):
        for label, value in items.items():
            new_item = QtGui.QStandardItem()
            new_item.setData(label, QtCore.Qt.DisplayRole)
            new_item.setData(value, IntentItemValue)

            self.setItem(self._item_count, new_item)
            self._item_count += 1


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
        self.beginInsertRows(
            QtCore.QModelIndex(),
            self.rowCount(),
            self.rowCount()
        )

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
        self.attr_schema = {
            IsOptional: "optional",
            Families: "families",
            Id: "id",
            Actions: "actions",
            Order: "order",

            # GUI-only data
            Type: "_type",
            Duration: "_duration",
            IsIdle: "_is_idle",
            IsProcessing: "_is_processing",
            HasProcessed: "_has_processed",
            HasSucceeded: "_has_succeeded",
            HasFailed: "_has_failed",
        }
        self.data_schema = {}

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


def error_from_result(result):
    error = result.get('error')

    if not error:
        return {}

    fname, line_no, func, exc = error.traceback
    return {
        "message": str(error),
        "fname": str(fname),
        "line_no": str(line_no),
        "func": str(func),
        "traceback": error.formatted_traceback
    }


class Plugin(Item):
    def __init__(self):
        super(Plugin, self).__init__()

        self.attr_schema.update({
            Label: "label",
            Name: "__name__",
            Icon: "icon",

            IsChecked: "active",
            Docstring: "__doc__",
            ActionIdle: "_action_idle",
            ActionFailed: "_action_failed",
            LogRecord: "_log",
            ErrorRecord: "_error",
            HasCompatible: "hasCompatible"
        })

    def append(self, item):

        item.label = item.label or item.__name__
        # Use class names if settings say so.
        if not settings.UseLabel:
            item.label = item.__name__

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

        item.hasCompatible = True

        return super(Plugin, self).append(item)

    def data(self, index, role):
        # This is because of bug without known cause
        # - on "reset" are called data for already removed indexes
        if index.row() >= len(self.items):
            return

        if role == QtCore.Qt.DisplayRole:
            role = Label
            if not settings.UseLabel:
                role = Name

        elif role == QtCore.Qt.DecorationRole:
            role = Icon

        item = self.items[index.row()]

        if role == Data:
            return {}

        elif role == Icon:
            return awesome.get(getattr(item, "icon", ""))

        elif role == ActionIconVisible:

            # Can only run actions on active plug-ins.
            if not item.active:
                return

            actions = list(item.actions)

            # Context specific actions
            for action in actions:
                if (
                    (item._has_failed and action.on == "failed") or
                    (item._has_succeeded and action.on == "succeeded") or
                    (item._has_processed and action.on == "processed") or
                    (not item._has_processed and action.on == "notProcessed")
                ):
                    return True
            return False

        elif role == Actions:

            # Can only run actions on active plug-ins.
            if not item.active:
                return

            actions = list(item.actions)

            valid_actions = []
            # Context specific actions
            for action in actions[:]:
                if (
                    (item._has_failed and action.on == "failed") or
                    (item._has_succeeded and action.on == "succeeded") or
                    (item._has_processed and action.on == "processed") or
                    (not item._has_processed and action.on == "notProcessed")
                ):
                    valid_actions.append(action)

            actions_len = len(valid_actions)
            if actions_len == 0:
                return valid_actions

            # Discard empty groups
            indexex_to_remove = []
            for idx, action in enumerate(valid_actions):
                if action.__type__ != "category":
                    continue

                next_id = idx + 1
                if next_id >= actions_len:
                    indexex_to_remove.append(idx)
                    continue

                next = valid_actions[next_id]
                if next.__type__ != "action":
                    indexex_to_remove.append(idx)

            for idx in reversed(indexex_to_remove):
                valid_actions.pop(idx)

            return valid_actions

        elif role == PathModule:
            return item.__module__

        elif role in self.attr_schema:
            key = self.attr_schema[role]
            return getattr(item, key, None)

        return super(Plugin, self).data(index, role)

    def setData(self, index, value, role):
        if role not in self.attr_schema:
            return super(Plugin, self).setData(index, value, role)

        key = self.attr_schema[role]
        item = self.items[index.row()]
        setattr(item, key, value)

        if __binding__ in ("PyQt4", "PySide"):
            self.dataChanged.emit(index, index)
        else:
            self.dataChanged.emit(index, index, [role])
        return True

    def update_with_result(self, result, action=False):
        item = result["plugin"]
        index = self.items.index(item)
        index = self.createIndex(index, 0)
        self.setData(index, False, IsIdle)
        self.setData(index, False, IsProcessing)
        self.setData(index, True, HasProcessed)
        self.setData(index, result["success"], HasSucceeded)

        records = index.data(LogRecord) or []
        records.extend(result.get('records', []))

        self.setData(index, records, LogRecord)

        # Once failed, never go back.
        if not self.data(index, HasFailed):
            self.setData(index, not result["success"], HasFailed)

        super(Plugin, self).update_with_result(result)

    def update_compatibility(self, context, instances):
        families = util.collect_families_from_instances(context, True)
        for plugin in self.items:
            has_compatible = False
            # A plugin should always show if it has processed.
            if plugin._has_processed:
                has_compatible = True
            elif plugin.__instanceEnabled__:
                compatibleInstances = pyblish.logic.instances_by_plugin(
                    context, plugin
                )
                for instance in instances:
                    if not instance.data.get("publish"):
                        continue

                    if instance in compatibleInstances:
                        has_compatible = True
                        break
            else:
                plugins = pyblish.logic.plugins_by_families(
                    [plugin], families
                )
                if plugins:
                    has_compatible = True

            plugin.hasCompatible = has_compatible


class Instance(Item):
    def __init__(self):
        super(Instance, self).__init__()

        self.ids = []
        self.data_schema.update({
            IsChecked: "publish",
            Label: "label",
            Name: "name",
            Icon: "icon",
        })
        self.attr_schema.update({
            LogRecord: "_log",
            ErrorRecord: "_error"
        })
        self.context_item = None

    def append(self, item):
        if getattr(item, '_type', None) == 'context':
            self.ids.append(item.id)
            self.context_item = item
            return super(Instance, self).append(item)

        item.optional = getattr(item, "optional", True)
        item.data["publish"] = item.data.get("publish", True)

        item.data["label"] = (
            getattr(item, "label", None) or
            item.data.get("label") or
            item.data["name"]
        )

        # Store instances id in easy access data member
        self.ids.append(item.id)

        # GUI-only data
        item._type = "instance"
        item._has_succeeded = False
        item._has_failed = False
        item._is_idle = True

        # Merge `family` and `families` for backwards compatibility
        family = item.data["family"]
        families = [f for f in item.data.get("families")] or []
        if family in families:
            families.remove(family)
        item.families = [family] + families
        return super(Instance, self).append(item)

    def data(self, index, role):
        # This is because of bug without known cause
        # - on "reset" are called data for already removed indexes
        if role == QtCore.Qt.DisplayRole:
            role = Label
            if not settings.UseLabel:
                role = Name

        elif role == QtCore.Qt.DecorationRole:
            role = Icon

        item = super(Instance, self).data(index, Object)
        if role == Object:
            return item

        elif role == Data:
            return item.data

        elif role == Icon:
            return awesome.get(item.data.get("icon"))

        elif role in self.attr_schema:
            key = self.attr_schema[role]
            return getattr(item, key, None)

        elif role in self.data_schema:
            key = self.data_schema[role]
            return item.data.get(key)

        return super(Instance, self).data(index, role)

    def setData(self, index, value, role):
        item = super(Instance, self).data(index, Object)

        if role in self.attr_schema:
            key = self.attr_schema[role]
            setattr(item, key, value)

            if __binding__ in ("PyQt4", "PySide"):
                self.dataChanged.emit(index, index)
            else:
                self.dataChanged.emit(index, index, [role])
            return True

        elif role in self.data_schema:
            key = self.data_schema[role]
            item.data[key] = value

            if __binding__ in ("PyQt4", "PySide"):
                self.dataChanged.emit(index, index)
            else:
                self.dataChanged.emit(index, index, [role])
            return True

        return super(Instance, self).setData(index, value, role)

    def update_with_result(self, result):
        item = result["instance"]

        if item is None:
            # for item in self.
            index = self.items.index(self.context_item)
            index = self.createIndex(index, 0)
        else:
            index = self.items.index(item)
            index = self.createIndex(index, 0)

        self.setData(index, False, IsIdle)
        self.setData(index, False, IsProcessing)
        self.setData(index, True, HasProcessed)
        self.setData(index, result["success"], HasSucceeded)
        records = index.data(LogRecord) or []
        records.extend(result.get('records', []))
        self.setData(index, records, LogRecord)
        self.setData(index, error_from_result(result), ErrorRecord)

        # Once failed, never go back.
        if not self.data(index, HasFailed):
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

            LogSize: 'size',

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
            ExcFunc: "func",
            ExcTraceback: "traceback",
        }

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            role = Label

        if role not in self.schema:
            return super(Terminal, self).data(index, role)

        item = self.items[index.row()]
        if role == Data:
            return item

        key = self.schema[role]
        value = item.get(key)

        if value is None:
            value = super(Terminal, self).data(index, role)

        return value

    def setData(self, index, value, role):
        item = self.items[index.row()]
        if role not in self.schema:
            return super(Terminal, self).setData(index, value, role)

        key = self.schema[role]
        item[key] = value

        if __binding__ in ("PyQt4", "PySide"):
            self.dataChanged.emit(index, index)
        else:
            self.dataChanged.emit(index, index, [role])
        return True

    def update_with_result(self, result):
        for record in result["records"]:
            ## Filtering should be in view
            # if record.levelno < settings.TerminalLoglevel:
            #     continue
            if isinstance(record, dict):
                self.append(record)
                continue

            self.append({
                "label": text_type(record.msg),
                "type": "record",
                "levelno": record.levelno,
                # Native
                "threadName": record.threadName,
                "name": record.name,
                "filename": record.filename,
                "pathname": record.pathname,
                "lineno": record.lineno,
                "msg": text_type(record.msg),
                "msecs": record.msecs,
                "levelname": record.levelname
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
        self.includes = {'families': ['*']}

    def item(self, index):
        index = self.index(index, 0, QtCore.QModelIndex())
        index = self.mapToSource(index)
        model = self.sourceModel()
        return model.items[index.row()]

    def reset(self):
        self.beginResetModel()
        self.includes = {'families': ['*']}
        self.endResetModel()

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

        # --- Check if any family assigned to the plugin is in allowed families
        for role, values in self.includes.items():
            includes_list = [([x] if isinstance(x, (list, tuple)) else x)
                             for x in getattr(item, role, None)]
            return any(include in values for include in includes_list)

        for role, values in self.excludes.items():
            data = getattr(item, role, None)
            if data in values:
                return False

        return super(ProxyModel, self).filterAcceptsRow(
            source_row, source_parent)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return super(ProxyModel, self).rowCount(parent)


class TreeItem(object):
    """Base class for an Item in the Group By Proxy"""
    def __init__(self):
        self._parent = None
        self._children = list()

    def parent(self):
        return self._parent

    def addChild(self, node):
        node._parent = self
        self._children.append(node)

    def rowCount(self):
        return len(self._children)

    def row(self):

        parent = self.parent()
        if not parent:
            return 0
        else:
            return self.parent().children().index(self)

    def columnCount(self):
        return 1

    def child(self, row):
        return self._children[row]

    def children(self):
        return self._children

    def data(self, role=QtCore.Qt.DisplayRole):
        return None


class ProxyTerminalItem(TreeItem):
    def __init__(self, source_index):
        self._expanded = False
        super(ProxyTerminalItem, self).__init__()
        self.model_index = source_index

    def setIsExpanded(self, in_bool):
        self._expanded = in_bool

    @property
    def expanded(self):
        return self._expanded

    def data(self, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            role = Label

        elif role == GroupObject:
            return self

        return self.model_index.data(role)


class ProxyTerminalDetail(TreeItem):
    def __init__(self, source_index):
        super(ProxyTerminalDetail, self).__init__()
        self.source_index = source_index

    def data(self, role=QtCore.Qt.DisplayRole):
        return self.source_index.data(role)


class TerminalProxy(QtCore.QAbstractProxyModel):
    """Proxy that groups by based on a specific role
    This assumes the source data is a flat list and not a tree.
    """

    def __init__(self):
        super(TerminalProxy, self).__init__()
        self.root = TreeItem()

    def flags(self, index):
        return (
            QtCore.Qt.ItemIsEnabled |
            QtCore.Qt.ItemIsSelectable
        )

    def rebuild(self):
        """Update proxy sections and items
        This should be called after changes in the source model that require
        changes in this list (for example new indices, less indices or update
        sections)
        """
        self.beginResetModel()
        # Start with new root node
        self.root = TreeItem()

        # Get indices from source model
        source = self.sourceModel()
        source_rows = source.rowCount()
        source_indexes = [source.index(i, 0) for i in range(source_rows)]

        for index in source_indexes:
            log_label = ProxyTerminalItem(index)
            if index.data(LogMessage) or index.data(Type) == 'error':
                log_item = ProxyTerminalDetail(index)
                log_label.addChild(log_item)
            self.root.addChild(log_label)

        self.endResetModel()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return

        node = index.internalPointer()

        if not node:
            return

        return node.data(role)

    def setData(self, in_index, data, role):
        source_idx = self.mapToSource(in_index)
        if not source_idx.isValid():
            return

        source_model = source_idx.model()
        node = in_index.internalPointer()

        if not node:
            return

        index = node.source_index
        source_model.setData(index, data, role)

        if __binding__ in ("PyQt4", "PySide"):
            self.dataChanged.emit(index, index)
        else:
            self.dataChanged.emit(index, index, [role])
        self.layoutChanged.emit()
        return True

    def is_header(self, index):
        """Return whether index is a header"""
        if index.isValid() and index.data(GroupObject):
            return True
        else:
            return False

    def mapFromSource(self, index):
        for section_item in self.root.children():
            for item in section_item.children():
                if item.source_index == index:
                    return self.createIndex(
                        item.row(), index.column(), item
                    )

        return QtCore.QModelIndex()

    def mapToSource(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        node = index.internalPointer()
        if not node:
            return QtCore.QModelIndex()

        if not hasattr(node, "source_index"):
            return QtCore.QModelIndex()
        return node.source_index

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def rowCount(self, parent):

        if not parent.isValid():
            node = self.root
        else:
            node = parent.internalPointer()

        if not node:
            return 0

        return node.rowCount()

    def index(self, row, column, parent):
        if parent and parent.isValid():
            parent_node = parent.internalPointer()
        else:
            parent_node = self.root

        item = parent_node.child(row)
        if item:
            return self.createIndex(row, column, item)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        node = index.internalPointer()
        if not node:
            return QtCore.QModelIndex()
        else:
            parent = node.parent()
            if not parent:
                return QtCore.QModelIndex()

            row = parent.row()
            return self.createIndex(row, 0, parent)
