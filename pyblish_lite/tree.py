
from .vendor import Qt
from Qt import QtWidgets, QtCore
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
        super(ProxySectionItem, self).__init__()
        self.label = "{0}".format(label)

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


class Proxy(QtWidgets.QAbstractProxyModel):
    """Proxy that groups by based on a specific role

    This assumes the source data is a flat list and not a tree.

    """

    def __init__(self):
        super(Proxy, self).__init__()
        self.root = Item()
        self.group_role = QtCore.Qt.DisplayRole

    def set_group_role(self, role):
        self.group_role = role

    def rebuild(self):
        """Update proxy sections and items

        This should be called after changes in the source model that require
        changes in this list (for example new indices, less indices or update
        sections)

        """

        # Start with new root node
        self.root = Item()

        # Get indices from source model
        source = self.sourceModel()
        source_rows = source.rowCount()
        source_indices = [source.index(i, 0) for i in range(source_rows)]

        def key_getter(source_index):
            """Return group role data for source index"""
            return source.data(source_index, self.group_role)

        for section, group in groupby(source_indices, key=key_getter):

            # section
            section_item = ProxySectionItem(section)
            self.root.addChild(section_item)

            #  items in section
            for i, index in enumerate(group):
                proxy_item = ProxyItem(index)
                section_item.addChild(proxy_item)

    def data(self, index, role=QtCore.Qt.DisplayRole):

        if not index.isValid():
            return

        node = index.internalPointer()

        if not node:
            return

        return node.data(role)

    def is_header(self, index):
        """Return whether index is a header"""
        if index in self.to_source:
            return False
        else:
            return True

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


class View(QtWidgets.QTreeView):
    # An item is requesting to be toggled, with optional forced-state
    toggled = QtCore.Signal("QModelIndex", object)

    # An item is requesting details
    inspected = QtCore.Signal("QModelIndex")

    def __init__(self, parent=None):
        super(View, self).__init__(parent)

        self.horizontalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        #self.setResizeMode(QtWidgets.QTreeView.Adjust)
        self.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setIndentation(10)
        #self.setItemsExpandable(False)

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
            if len(indexes) <= 1 and event.pos().x() < 20:
                for index in indexes:
                    self.toggled.emit(index, None)

        return super(View, self).mouseReleaseEvent(event)
