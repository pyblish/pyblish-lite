import pyblish

from . import model
from .vendor.Qt import QtWidgets, QtCore, __binding__
from itertools import groupby


class Item(object):
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


class ProxyItem(Item):
    def __init__(self, source_index):
        super(ProxyItem, self).__init__()
        self.source_index = source_index

    def data(self, role=QtCore.Qt.DisplayRole):
        return self.source_index.data(role)


class ProxySectionItem(Item):
    def __init__(self, label):
        self._expanded = True
        super(ProxySectionItem, self).__init__()
        self.label = "{0}".format(label)

    def setIsExpanded(self, in_bool):
        self._expanded = in_bool

    @property
    def expanded(self):
        return self._expanded

    def data(self, role=QtCore.Qt.DisplayRole):

        if role == QtCore.Qt.DisplayRole:
            return self.label

        elif role == QtCore.Qt.FontRole:
            font = QtWidgets.QFont()
            font.setPointSize(10)
            font.setWeight(900)
            return font

        elif role == QtCore.Qt.TextColorRole:
            return QtWidgets.QColor(50, 20, 20)

        elif role == QtCore.Qt.BackgroundColorRole:
            return QtWidgets.QColor(220, 220, 220)

        elif role == model.GroupObject:
            return self


class Proxy(QtCore.QAbstractProxyModel):
    """Proxy that groups by based on a specific role
    This assumes the source data is a flat list and not a tree.
    """

    def __init__(self):
        super(Proxy, self).__init__()
        self.root = Item()
        self.group_role = QtCore.Qt.DisplayRole

    def set_group_role(self, role):
        self.group_role = role

    def flags(self, index):
        return (
            QtCore.Qt.ItemIsEnabled |
            QtCore.Qt.ItemIsSelectable
        )
        
    def groupby_key(self, source_index):
        """Returns the data to group by.
        Override this in subclasses to group by customized data instead of
        by simply the currently set group role.
        Args:
            source_index (QtCore.QModelIndex): index from source to retrieve
                data from to group by.
        Returns:
            object: Collected data to group by for index.
        """
        return source_index.data(self.group_role)

    def groupby_label(self, section):
        """Returns the label for a section based on the collected group key.
        Override this in subclasses to format the name for a specific key.
        Args:
            section: key value for this group section
        Returns:
            str: Label of the section header based on group key
        """
        return section

    def rebuild(self):
        """Update proxy sections and items
        This should be called after changes in the source model that require
        changes in this list (for example new indices, less indices or update
        sections)
        """
        self.beginResetModel()
        # Start with new root node
        self.root = Item()

        # Get indices from source model
        source = self.sourceModel()
        source_rows = source.rowCount()
        source_indices = [source.index(i, 0) for i in range(source_rows)]

        for section, group in groupby(source_indices,
                                      key=self.groupby_key):

            # section
            label = self.groupby_label(section)
            section_item = ProxySectionItem(label)
            self.root.addChild(section_item)

            #  items in section
            for i, index in enumerate(group):
                proxy_item = ProxyItem(index)
                section_item.addChild(proxy_item)
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

    def is_header(self, index):
        """Return whether index is a header"""
        if index.isValid() and not self.mapToSource(index).isValid():
            return True
        else:
            return False

    def mapFromSource(self, index):
        for section_item in self.root.children():
            for item in section_item.children():
                if item.source_index == index:
                    return self.createIndex(item.row(),
                                            index.column(),
                                            item)

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


class PluginOrderGroupProxy(Proxy):
    """Proxy grouping by order by full range known.
    Before Collectors and after Integrators will be grouped as "Other".
    """

    def groupby_key(self, source_index):
        plugin_order = super(
            PluginOrderGroupProxy, self
        ).groupby_key(source_index)
        label = "Other"

        mapping = {pyblish.plugin.CollectorOrder: "Collector",
                   pyblish.plugin.ValidatorOrder: "Validator",
                   pyblish.plugin.ExtractorOrder: "Extractor",
                   pyblish.plugin.IntegratorOrder: "Integrator"}
        for order, _type in mapping.items():
            if pyblish.lib.inrange(plugin_order, base=order):
                label = _type

        return label


class FamilyGroupProxy(Proxy):
    """Proxy grouping by order by full range known.
    Before Collectors and after Integrators will be grouped as "Other".
    """

    def groupby_key(self, source_index):
        families = super(FamilyGroupProxy, self).groupby_key(source_index)
        family = families[0]
        return family


class View(QtWidgets.QTreeView):
    # An item is requesting to be toggled, with optional forced-state
    toggled = QtCore.Signal("QModelIndex", object)
    show_perspective = QtCore.Signal("QModelIndex")
    # An item is requesting details
    inspected = QtCore.Signal("QModelIndex")

    def __init__(self, parent=None):
        super(View, self).__init__(parent)

        self.horizontalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setIndentation(0)

        self.expanded.connect(self.change_expanded)
        self.collapsed.connect(self.change_expanded)

    def change_expanded(self, index):
        group = index.data(model.GroupObject)
        if group:
            group.setIsExpanded(self.isExpanded(index))

    def event(self, event):
        if not event.type() == QtCore.QEvent.KeyPress:
            return super(View, self).event(event)

        elif event.key() == QtCore.Qt.Key_Space:
            for index in self.selectionModel().selectedIndexes():
                self.toggled.emit(index, None)

            return True

        elif event.key() == QtCore.Qt.Key_Backspace:
            for index in self.selectionModel().selectedIndexes():
                self.toggled.emit(index, False)

            return True

        elif event.key() == QtCore.Qt.Key_Return:
            for index in self.selectionModel().selectedIndexes():
                self.toggled.emit(index, True)

            return True

        return super(View, self).event(event)

    def focusOutEvent(self, event):
        self.selectionModel().clear()

    def leaveEvent(self, event):
        self._inspecting = False
        super(View, self).leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            self.inspected.emit(index) if index.isValid() else None

        return super(View, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            indexes = self.selectionModel().selectedIndexes()
            if len(indexes) == 1:
                index = indexes[0]
                # If instance or Plugin
                if index.data(model.Object) is not None:
                    if event.pos().x() < 20:
                        self.toggled.emit(index, None)
                    if event.pos().x() > self.width()-20:
                        self.show_perspective.emit(index)
                else:
                    if event.pos().x() < 20:
                        if self.isExpanded(index):
                            self.collapse(index)
                        else:
                            self.expand(index)
                    else:
                        # TODO: select all children
                        pass
                    self.clearSelection()
            # Deselect all group labels
            if len(indexes) > 0:
                for index in indexes:
                    if index.data(model.Object) is None:
                        self.selectionModel().select(
                            index, QtCore.QItemSelectionModel.Deselect
                        )

        return super(View, self).mouseReleaseEvent(event)
