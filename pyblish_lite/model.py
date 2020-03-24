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

import pyblish

from . import settings, util
from .awesome import tags as awesome
from .vendor.Qt import QtCore, QtGui, __binding__
from .vendor.six import text_type
from .constants import PluginStates, InstanceStates, GroupStates, Roles

try:
    from pypeapp import config
    get_presets = config.get_presets
except Exception:
    get_presets = dict

# ItemTypes
ItemType = QtGui.QStandardItem.UserType
GroupType = QtGui.QStandardItem.UserType + 1


class QAwesomeIconFactory:
    icons = {}
    @classmethod
    def icon(cls, icon_name):
        if icon_name not in cls.icons:
            cls.icons[icon_name] = awesome.get(icon_name)
        return cls.icons[icon_name]


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
        self.default_index = 0

    @property
    def has_items(self):
        return self._item_count > 0

    def reset(self):
        self.clear()
        self._item_count = 0
        self.default_index = 0

        intents_preset = (
            get_presets()
            .get("tools", {})
            .get("pyblish", {})
            .get("ui", {})
            .get("intents", {})
        )
        default = intents_preset.get("default")
        items = intents_preset.get("items", {})
        if not items:
            return

        for idx, item_value in enumerate(items.keys()):
            if item_value == default:
                self.default_index = idx
                break

        self.add_items(items)

    def add_items(self, items):
        for value, label in items.items():
            new_item = QtGui.QStandardItem()
            new_item.setData(label, QtCore.Qt.DisplayRole)
            new_item.setData(value, Roles.IntentItemValue)

            self.setItem(self._item_count, new_item)
            self._item_count += 1


class PluginItem(QtGui.QStandardItem):
    """Plugin item implementation."""

    def __init__(self, plugin):
        super(PluginItem, self).__init__()

        item_text = plugin.__name__
        if settings.UseLabel:
            if hasattr(plugin, "label") and plugin.label:
                item_text = plugin.label

        self.plugin = plugin

        self.setData(plugin, Roles.ObjectRole)
        self.setData(item_text, QtCore.Qt.DisplayRole)
        self.setData(False, Roles.IsEnabledRole)
        self.setData(0, Roles.PublishFlagsRole)

        icon_name = ""
        if hasattr(plugin, "icon") and plugin.icon:
            icon_name = plugin.icon
        icon = QAwesomeIconFactory.icon(icon_name)
        self.setData(icon, QtCore.Qt.DecorationRole)

        actions = []
        if hasattr(plugin, "actions") and plugin.actions:
            actions = list(plugin.actions)
        plugin.actions = actions

        is_checked = True
        is_optional = getattr(plugin, "optional", False)
        if is_optional:
            is_checked = getattr(plugin, "active", True)

        plugin.active = is_checked
        plugin.optional = is_optional

        self.setFlags(
            QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        )

    def type(self):
        return ItemType

    def data(self, role=QtCore.Qt.DisplayRole):
        if role == Roles.ItemRole:
            return self

        if role == Roles.IsOptionalRole:
            return self.plugin.optional

        if role == Roles.ObjectRole:
            return self.plugin

        if role == Roles.TypeRole:
            return self.type()

        if role == QtCore.Qt.CheckStateRole:
            return self.plugin.active

        if role == Roles.PathModuleRole:
            return self.plugin.__module__

        if role == Roles.FamiliesRole:
            return self.plugin.families

        if role == Roles.DocstringRole:
            return self.plugin.__doc__

        if role == Roles.PluginActionsVisibleRole:
            # Can only run actions on active plug-ins.
            if not self.plugin.active or not self.plugin.actions:
                return False

            publish_states = self.data(Roles.PublishFlagsRole)
            if (
                not publish_states & PluginStates.IsCompatible
                or publish_states & PluginStates.WasSkipped
            ):
                return False

            # Context specific actions
            for action in self.plugin.actions:
                if action.on == "failed":
                    if publish_states & PluginStates.HasError:
                        return True

                elif action.on == "succeeded":
                    if (
                        publish_states & PluginStates.WasProcessed
                        and not publish_states & PluginStates.HasError
                    ):
                        return True

                elif action.on == "processed":
                    if publish_states & PluginStates.WasProcessed:
                        return True

                elif action.on == "notProcessed":
                    if not publish_states & PluginStates.WasProcessed:
                        return True

            return False

        if role == Roles.PluginValidActionsRole:
            valid_actions = []

            # Can only run actions on active plug-ins.
            if not self.plugin.active or not self.plugin.actions:
                return valid_actions

            if not self.plugin.active or not self.plugin.actions:
                return False

            publish_states = self.data(Roles.PublishFlagsRole)
            if (
                not publish_states & PluginStates.IsCompatible
                or publish_states & PluginStates.WasSkipped
            ):
                return False

            # Context specific actions
            for action in self.plugin.actions:
                valid = False
                if action.on == "failed":
                    if publish_states & PluginStates.HasError:
                        valid = True

                elif action.on == "succeeded":
                    if (
                        publish_states & PluginStates.WasProcessed
                        and not publish_states & PluginStates.HasError
                    ):
                        valid = True

                elif action.on == "processed":
                    if publish_states & PluginStates.WasProcessed:
                        valid = True

                elif action.on == "notProcessed":
                    if not publish_states & PluginStates.WasProcessed:
                        valid = True

                if valid:
                    valid_actions.append(action)

            if not valid_actions:
                return valid_actions

            actions_len = len(valid_actions)
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

        return super(PluginItem, self).data(role)

    def setData(self, value, role=(QtCore.Qt.UserRole + 1)):
        if role == QtCore.Qt.CheckStateRole:
            if not self.data(Roles.IsEnabledRole):
                return False
            self.plugin.active = value
            self.emitDataChanged()
            return True

        if role == Roles.PublishFlagsRole:
            if isinstance(value, list):
                _value = self.data(Roles.PublishFlagsRole)
                for flag in value:
                    _value |= flag
                value = _value

            elif isinstance(value, dict):
                _value = self.data(Roles.PublishFlagsRole)
                for flag, _bool in value.items():
                    if _bool is True:
                        _value |= flag
                    elif _value & flag:
                        _value ^= flag
                value = _value

            if value & PluginStates.HasWarning:
                if self.parent():
                    self.parent().setData(
                        {GroupStates.HasWarning: True},
                        Roles.PublishFlagsRole
                    )
            if value & PluginStates.HasError:
                if self.parent():
                    self.parent().setData(
                        {GroupStates.HasError: True},
                        Roles.PublishFlagsRole
                    )

        return super(PluginItem, self).setData(value, role)


class GroupItem(QtGui.QStandardItem):
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop("order", None)
        self.publish_states = 0
        super(GroupItem, self).__init__(*args, **kwargs)

    def flags(self):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def data(self, role=QtCore.Qt.DisplayRole):
        if role == Roles.PublishFlagsRole:
            return self.publish_states

        if role == Roles.ItemRole:
            return self

        if role == Roles.TypeRole:
            return self.type()

        return super(GroupItem, self).data(role)

    def setData(self, value, role=(QtCore.Qt.UserRole + 1)):
        if role == Roles.PublishFlagsRole:
            if isinstance(value, list):
                _value = self.data(Roles.PublishFlagsRole)
                for flag in value:
                    _value |= flag
                value = _value

            elif isinstance(value, dict):
                _value = self.data(Roles.PublishFlagsRole)
                for flag, _bool in value.items():
                    if _bool is True:
                        _value |= flag
                    elif _value & flag:
                        _value ^= flag
                value = _value
            self.publish_states = value
            self.emitDataChanged()
            return True

        return super(GroupItem, self).setData(value, role)

    def type(self):
        return GroupType


class PluginModel(QtGui.QStandardItemModel):
    def __init__(self, controller, *args, **kwargs):
        super(PluginModel, self).__init__(*args, **kwargs)

        self.controller = controller
        self.checkstates = {}
        self.group_items = {}
        self.plugin_items = {}

    def reset(self):
        self.group_items = {}
        self.plugin_items = {}
        self.clear()

    def append(self, plugin):
        plugin_groups = self.controller.order_groups.groups()
        label = None
        order = None
        for _order, _label in reversed(plugin_groups.items()):
            if order is None or plugin.order < _order:
                label = _label
                order = _order
            else:
                break

        if label is None:
            label = "Other"

        if order is None:
            order = 99999999999999

        group_item = self.group_items.get(label)
        if not group_item:
            group_item = GroupItem(label, order=order)
            self.appendRow(group_item)
            self.group_items[label] = group_item

        new_item = PluginItem(plugin)
        group_item.appendRow(new_item)

        self.plugin_items[plugin._id] = new_item

    def store_checkstates(self):
        self.checkstates.clear()

        for plugin_item in self.plugin_items.values():
            if not plugin_item.plugin.optional:
                continue
            mod = plugin_item.plugin.__module__
            class_name = plugin_item.plugin.__class__.__name__
            uid = "{}.{}".format(mod, class_name)

            self.checkstates[uid] = plugin_item.data(QtCore.Qt.CheckStateRole)

    def restore_checkstates(self):
        for plugin_item in self.plugin_items.values():
            if not plugin_item.plugin.optional:
                continue
            mod = plugin_item.plugin.__module__
            class_name = plugin_item.plugin.__class__.__name__
            uid = "{}.{}".format(mod, class_name)

            state = self.checkstates.get(uid)
            if state is not None:
                plugin_item.setData(state, QtCore.Qt.CheckStateRole)

    def update_with_result(self, result, action=False):
        plugin = result["plugin"]
        item = self.plugin_items[plugin._id]

        new_flag_states = {
            PluginStates.InProgress: False,
            PluginStates.WasProcessed: True
        }

        publish_states = item.data(Roles.PublishFlagsRole)

        has_warning = publish_states & PluginStates.HasWarning
        new_records = result.get("records") or []
        if not has_warning:
            for record in new_records:
                if not hasattr(record, "levelname"):
                    continue

                if str(record.levelname).lower() in [
                    "warning", "critical", "error"
                ]:
                    new_flag_states[PluginStates.HasWarning] = True
                    break

        if (
            not publish_states & PluginStates.HasError
            and not result["success"]
        ):
            new_flag_states[PluginStates.HasError] = True

        item.setData(new_flag_states, Roles.PublishFlagsRole)

        records = item.data(Roles.LogRecordsRole) or []
        records.extend(new_records)

        item.setData(new_records, Roles.LogRecordsRole)

    def update_compatibility(self):
        context = self.controller.context

        families = util.collect_families_from_instances(context, True)
        for plugin_item in self.plugin_items.values():
            publish_states = plugin_item.data(Roles.PublishFlagsRole)
            if (
                publish_states & PluginStates.WasProcessed
                or publish_states & PluginStates.WasSkipped
            ):
                continue

            is_compatible = False
            # A plugin should always show if it has processed.
            if plugin_item.plugin.__instanceEnabled__:
                compatible_instances = pyblish.logic.instances_by_plugin(
                    context, plugin_item.plugin
                )
                for instance in context:
                    if not instance.data.get("publish"):
                        continue

                    if instance in compatible_instances:
                        is_compatible = True
                        break
            else:
                plugins = pyblish.logic.plugins_by_families(
                    [plugin_item.plugin], families
                )
                if plugins:
                    is_compatible = True

            current_is_compatible = publish_states & PluginStates.IsCompatible
            if (
                (is_compatible and not current_is_compatible)
                or (not is_compatible and current_is_compatible)
            ):
                new_flag = {
                    PluginStates.IsCompatible: is_compatible
                }
                plugin_item.setData(new_flag, Roles.PublishFlagsRole)


class PluginFilterProxy(QtCore.QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        item = source_parent.child(source_row, 0)
        item_type = item.data(Roles.TypeRole)
        if item_type != ItemType:
            return True

        publish_states = item.data(Roles.PublishFlagsRole)
        if (
            publish_states & PluginStates.WasSkipped
            or not publish_states & PluginStates.IsCompatible
        ):
            return False
        return True


class InstanceItem(QtGui.QStandardItem):
    """Plugin item implementation."""

    def __init__(self, instance):
        super(InstanceItem, self).__init__()

        self.is_context = False
        publish_states = getattr(instance, "_publish_states", 0)
        if publish_states & InstanceStates.ContextType:
            self.is_context = True

        instance._publish_states = publish_states
        instance.optional = getattr(instance, "optional", True)
        instance.data["publish"] = instance.data.get("publish", True)
        instance.data["label"] = (
            instance.data.get("label")
            or getattr(instance, "label", None)
            or instance.data["name"]
        )
        self.instance = instance

    def flags(self):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def type(self):
        return ItemType

    def data(self, role=QtCore.Qt.DisplayRole):
        if role == Roles.TypeRole:
            return self.type()

        if role == QtCore.Qt.DisplayRole:
            if settings.UseLabel:
                return self.instance.data["label"]
            return self.instance.data["name"]

        if role == QtCore.Qt.DecorationRole:
            icon_name = self.instance.data.get("icon") or "file"
            return QAwesomeIconFactory.icon(icon_name)

        if role == Roles.TypeRole:
            return self.type()

        if role == Roles.IsEnabledRole:
            return self.instance.optional

        if role == Roles.FamiliesRole:
            if self.is_context:
                return ["Context"]

            families = []
            family = self.instance.data.get("family")
            if family:
                families.append(family)

            _families = self.instance.data.get("families") or []
            for _family in _families:
                if _family not in families:
                    families.append(_family)

            return families

        if role == Roles.ItemRole:
            return self

        if role == Roles.IsOptionalRole:
            return self.instance.optional

        if role == Roles.ObjectRole:
            return self.instance

        if role == QtCore.Qt.CheckStateRole:
            return self.instance.data["publish"]

        if role == Roles.PublishFlagsRole:
            return self.instance._publish_states

        return super(InstanceItem, self).data(role)

    def setData(self, value, role=(QtCore.Qt.UserRole + 1)):
        if role == QtCore.Qt.CheckStateRole:
            if not self.data(Roles.IsEnabledRole):
                return False
            self.instance.data["publish"] = value
            self.emitDataChanged()
            return True

        if role == Roles.PublishFlagsRole:
            if isinstance(value, list):
                _value = self.instance._publish_states
                for flag in value:
                    _value |= flag
                value = _value

            elif isinstance(value, dict):
                _value = self.instance._publish_states
                for flag, _bool in value.items():
                    if _bool is True:
                        _value |= flag
                    elif _value & flag:
                        _value ^= flag
                value = _value

            self.instance._publish_states = value
            self.emitDataChanged()
            return True

        return super(InstanceItem, self).setData(value, role)


class InstanceOverviewModel(QtGui.QStandardItemModel):
    def __init__(self, controller, *args, **kwargs):
        super(InstanceOverviewModel, self).__init__(*args, **kwargs)

        self.controller = controller
        self.checkstates = {}
        self.group_items = {}
        self.instance_items = {}

    def reset(self):
        self.group_items = {}
        self.instance_items = {}
        self.clear()

    def append(self, instance):
        new_item = InstanceItem(instance)
        families = new_item.data(Roles.FamiliesRole)
        group_item = self.group_items.get(families[0])
        if not group_item:
            group_item = GroupItem(families[0])
            self.appendRow(group_item)
            self.group_items[families[0]] = group_item

        group_item.appendRow(new_item)
        instance_id = instance.id
        self.instance_items[instance_id] = new_item

    def store_checkstates(self):
        self.checkstates.clear()

        for instance_item in self.instance_items.values():
            if not instance_item.instance.optional:
                continue
            family = instance_item.data(Roles.FamiliesRole)[0]
            name = instance_item.instance.data["name"]
            uid = "{}.{}".format(family, name)

            self.checkstates[uid] = instance_item.data(
                QtCore.Qt.CheckStateRole
            )

    def restore_checkstates(self):
        for instance_item in self.instance_items.values():
            if not instance_item.instance.optional:
                continue
            family = instance_item.data(Roles.FamiliesRole)[0]
            name = instance_item.instance.data["name"]
            uid = "{}.{}".format(family, name)

            state = self.checkstates.get(uid)
            if state is not None:
                instance_item.setData(state, QtCore.Qt.CheckStateRole)

    def update_with_result(self, result, action=False):
        instance = result["instance"]
        if instance is None:
            instance_id = self.controller.context.id
        else:
            instance_id = instance.id

        item = self.instance_items[instance_id]

        new_flag_states = {
            InstanceStates.InProgress: False
        }

        publish_states = item.data(Roles.PublishFlagsRole)
        has_warning = publish_states & InstanceStates.HasWarning
        new_records = result.get("records") or []
        if not has_warning:
            for record in new_records:
                if not hasattr(record, "levelname"):
                    continue

                if str(record.levelname).lower() in [
                    "warning", "critical", "error"
                ]:
                    new_flag_states[InstanceStates.HasWarning] = True
                    break

        if (
            not publish_states & InstanceStates.HasError
            and not result["success"]
        ):
            new_flag_states[InstanceStates.HasError] = True

        item.setData(new_flag_states, Roles.PublishFlagsRole)

        records = item.data(Roles.LogRecordsRole) or []
        records.extend(new_records)

        item.setData(new_records, Roles.LogRecordsRole)

    def update_compatibility(self, context, instances):
        families = util.collect_families_from_instances(context, True)
        for plugin_item in self.plugin_items.values():
            publish_states = plugin_item.data(Roles.PublishFlagsRole)
            if (
                publish_states & PluginStates.WasProcessed
                or publish_states & PluginStates.WasSkipped
            ):
                continue

            is_compatible = False
            # A plugin should always show if it has processed.
            if plugin_item.plugin.__instanceEnabled__:
                compatibleInstances = pyblish.logic.instances_by_plugin(
                    context, plugin_item.plugin
                )
                for instance in instances:
                    if not instance.data.get("publish"):
                        continue

                    if instance in compatibleInstances:
                        is_compatible = True
                        break
            else:
                plugins = pyblish.logic.plugins_by_families(
                    [plugin_item.plugin], families
                )
                if plugins:
                    is_compatible = True

            current_is_compatible = publish_states & PluginStates.IsCompatible
            if (
                (is_compatible and not current_is_compatible)
                or (not is_compatible and current_is_compatible)
            ):
                plugin_item.setData(
                    {PluginStates.IsCompatible: is_compatible},
                    Roles.PublishFlagsRole
                )


class InstanceArtistModel(QtGui.QStandardItemModel):
    def __init__(self, *args, **kwargs):
        super(InstanceArtistModel, self).__init__(*args, **kwargs)
        self.instance_items = {}

    def on_item_changed(self, item):
        my_item = self.instance_items[item.instance.id]
        my_item.emitDataChanged()

    def reset(self):
        self.instance_items = {}
        self.clear()

    def append(self, instance):
        new_item = InstanceItem(instance)
        self.appendRow(new_item)
        self.instance_items[instance.id] = new_item


class Abstract(QtCore.QAbstractListModel):
    def __iter__(self):
        """Yield each row of model"""
        for index in range(len(self.items)):
            yield self.createIndex(index, 0)

    def data(self, index, role):
        if role == Roles.ObjectRole:
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


class Terminal(Abstract):
    def __init__(self, parent=None):
        super(Terminal, self).__init__(parent)
        self.items = list()

        # Common schema
        self.schema = {
            Roles.TypeRole: "type",
            Roles.Label: "label",

            Roles.LogSize: 'size',

            # Records
            Roles.LogThreadName: "threadName",
            Roles.LogName: "name",
            Roles.LogFilename: "filename",
            Roles.LogPath: "pathname",
            Roles.LogLineNumber: "lineno",
            Roles.LogMessage: "msg",
            Roles.LogMilliseconds: "msecs",
            Roles.LogLevel: "levelname",

            # Exceptions
            Roles.ExcFunc: "func",
            Roles.ExcTraceback: "traceback",
        }

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            role = Roles.Label

        if role not in self.schema:
            return super(Terminal, self).data(index, role)

        item = self.items[index.row()]
        if role == Roles.ItemRole:
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

        args = [index, index]
        if __binding__ not in ("PyQt4", "PySide"):
            args.append([role])
        self.dataChanged.emit(*args)
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
        self.model_index = source_index
        super(ProxyTerminalItem, self).__init__()

    def setIsExpanded(self, in_bool):
        if self.model_index.data(Roles.ObjectRole).get("type") == "info":
            return
        self._expanded = in_bool

    @property
    def expanded(self):
        return self._expanded

    def data(self, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            role = Roles.Label

        elif role == Roles.GroupObjectRole:
            return self

        return self.model_index.data(role)


class ProxyTerminalDetail(TreeItem):
    def __init__(self, source_index):
        self.source_index = source_index
        super(ProxyTerminalDetail, self).__init__()

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
            if (
                index.data(Roles.LogMessage)
                or index.data(Roles.TypeRole) == 'error'
            ):
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
        if index.isValid() and index.data(Roles.GroupObjectRole):
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

    def rowCount(self, parent=None):

        if not parent or not parent.isValid():
            node = self.root
        else:
            node = parent.internalPointer()

        if not node:
            return 0

        return node.rowCount()

    def index(self, row, column, parent=None):
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
