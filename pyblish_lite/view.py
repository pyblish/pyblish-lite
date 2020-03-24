import sys
from .vendor.Qt import QtCore, QtWidgets, QtGui
from . import model, delegate
from .constants import PluginStates, InstanceStates, Roles


class Item(QtWidgets.QListView):
    # An item is requesting to be toggled, with optional forced-state
    toggled = QtCore.Signal(QtCore.QModelIndex, object)
    show_perspective = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        super(Item, self).__init__(parent)

        self.horizontalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setVerticalScrollMode(QtWidgets.QListView.ScrollPerPixel)

    def event(self, event):
        if not event.type() == QtCore.QEvent.KeyPress:
            return super(Item, self).event(event)

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

        return super(Item, self).event(event)

    def focusOutEvent(self, event):
        self.selectionModel().clear()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            indexes = self.selectionModel().selectedIndexes()
            if len(indexes) <= 1 and event.pos().x() < 20:
                for index in indexes:
                    self.toggled.emit(index, None)
            if len(indexes) == 1 and event.pos().x() > self.width()-40:
                for index in indexes:
                    self.show_perspective.emit(index)

        return super(Item, self).mouseReleaseEvent(event)


class OverviewView(QtWidgets.QTreeView):
    # An item is requesting to be toggled, with optional forced-state
    toggled = QtCore.Signal(QtCore.QModelIndex, object)
    show_perspective = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        super(OverviewView, self).__init__(parent)

        self.horizontalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setItemsExpandable(True)
        self.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setIndentation(0)

    def event(self, event):
        if not event.type() == QtCore.QEvent.KeyPress:
            return super(OverviewView, self).event(event)

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

        return super(OverviewView, self).event(event)

    def focusOutEvent(self, event):
        self.selectionModel().clear()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            indexes = self.selectionModel().selectedIndexes()
            if len(indexes) == 1:
                index = indexes[0]
                # If instance or Plugin
                item = index.data(Roles.ItemRole)
                if item.type() in (model.InstanceType, model.PluginType):
                    if event.pos().x() < 20:
                        self.toggled.emit(index, None)
                    elif event.pos().x() > self.width() - 20:
                        self.show_perspective.emit(index)
                else:
                    # self.setExpanded(index, self.isExpanded(index))
                    if self.isExpanded(index):
                        self.collapse(index)
                    else:
                        self.expand(index)

                    self.selectionModel().select(
                        index, QtCore.QItemSelectionModel.Deselect
                    )

            # Deselect all group labels
            for index in indexes:
                item = index.data(Roles.ItemRole)
                if item.type() == model.GroupType:
                    self.selectionModel().select(
                        index, QtCore.QItemSelectionModel.Deselect
                    )

        return super(OverviewView, self).mouseReleaseEvent(event)


class TerminalView(QtWidgets.QTreeView):
    # An item is requesting to be toggled, with optional forced-state
    toggled = QtCore.Signal(QtCore.QModelIndex, object)

    def __init__(self, parent=None):
        super(TerminalView, self).__init__(parent)

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
        group = index.data(Roles.GroupObjectRole)
        if group:
            group.setIsExpanded(self.isExpanded(index))
        self.model().layoutChanged.emit()
        self.updateGeometry()

    def event(self, event):
        if not event.type() == QtCore.QEvent.KeyPress:
            return super(TerminalView, self).event(event)

        elif event.key() == QtCore.Qt.Key_Space:
            for index in self.selectionModel().selectedIndexes():
                if self.isExpanded(index):
                    self.collapse(index)
                else:
                    self.expand(index)

            return True

        elif event.key() == QtCore.Qt.Key_Backspace:
            for index in self.selectionModel().selectedIndexes():
                self.collapse(index)

            return True

        elif event.key() == QtCore.Qt.Key_Return:
            for index in self.selectionModel().selectedIndexes():
                self.expand(index)

            return True

        return super(TerminalView, self).event(event)

    def focusOutEvent(self, event):
        self.selectionModel().clear()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            indexes = self.selectionModel().selectedIndexes()
            if len(indexes) == 1:
                index = indexes[0]
                if index.data(Roles.GroupObjectRole):
                    if self.isExpanded(index):
                        self.collapse(index)
                    else:
                        self.expand(index)

            # Deselect all group labels
            if len(indexes) > 0:
                for index in indexes:
                    if index.data(Roles.GroupObjectRole):
                        self.selectionModel().select(
                            index, QtCore.QItemSelectionModel.Deselect
                        )

        return super(TerminalView, self).mouseReleaseEvent(event)

    def sizeHint(self):
        size = super(TerminalView, self).sizeHint()
        height = 0
        for idx in range(self.model().rowCount()):
            index = self.model().index(idx, 0)
            height += self.rowHeight(index)
            item = index.data(Roles.GroupObjectRole)
            if item.expanded:
                index = self.model().index(0, 1, index)
                height += self.rowHeight(index)
        size.setHeight(height)
        return size

    def rowsInserted(self, parent, start, end):
        """Automatically scroll to bottom on each new item added

        Arguments:
            parent (QtCore.QModelIndex): The model itself, since this is a list
            start (int): Start index of item
            end (int): End index of item

        """

        super(TerminalView, self).rowsInserted(parent, start, end)

        # IMPORTANT: This must be done *after* the superclass to get
        # an accurate value of the delegate's height.
        self.scrollToBottom()


class EllidableLabel(QtWidgets.QLabel):
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(
            self.text(), QtCore.Qt.ElideRight, self.width()
        )
        painter.drawText(self.rect(), self.alignment(), elided)


class PerspectiveWidget(QtWidgets.QWidget):
    l_doc = '   Documentation'
    l_rec = '   Records'
    l_path = '   Path'
    indicator_colors = {
        "idle": {
            "bg": "#ffffff",
            "font": "#333333"
        },
        "active": {
            "bg": "#99CEEE",
            "font": "#ffffff"
        },
        "error": {
            "bg": "#cc4a4a",
            "font": "#ffffff"
        },
        "ok": {
            "bg": "#69a567",
            "font": "#ffffff"
        },
        "warning": {
            "bg": "#ff9900",
            "font": "#ffffff"
        }
    }

    def __init__(self, parent):
        super(PerspectiveWidget, self).__init__(parent)
        # self.setStyleSheet("border:1px solid rgb(0, 255, 0); ")
        self.parent_widget = parent
        main_layout = QtWidgets.QVBoxLayout(self)

        header_widget = QtWidgets.QWidget()
        toggle_button = QtWidgets.QPushButton(parent=header_widget)
        toggle_button.setObjectName("PerspectiveToggleBtn")
        toggle_button.setText(delegate.icons["angle-left"])
        toggle_button.setMinimumHeight(50)
        toggle_button.setFixedWidth(40)

        indicator = QtWidgets.QLabel('', parent=header_widget)
        indicator.setFixedWidth(30)
        indicator.setAlignment(QtCore.Qt.AlignCenter)

        name = EllidableLabel('*Name of inspected', parent=header_widget)
        name.setStyleSheet(
            "font-size: 16pt;"
            "font-style: bold;"
            "font-weight: 50;"
        )

        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setAlignment(QtCore.Qt.AlignLeft)
        header_layout.addWidget(toggle_button)
        header_layout.addWidget(indicator)
        header_layout.addWidget(name)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        header_widget.setLayout(header_layout)

        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.addWidget(header_widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)

        documentation = ExpandableWidget(self, self.l_doc)
        layout.addWidget(documentation)

        path = ExpandableWidget(self, self.l_path)
        layout.addWidget(path)

        records = ExpandableWidget(self, self.l_rec)
        layout.addWidget(records)

        scroll_widget = QtWidgets.QScrollArea(self)
        contents_widget = QtWidgets.QWidget(scroll_widget)
        contents_widget.setLayout(layout)
        contents_widget.setStyleSheet(
            'padding: 0px;'
            'background: "#444";'
        )
        contents_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )

        scroll_widget.setWidgetResizable(True)
        scroll_widget.setWidget(contents_widget)
        self.indicator = indicator
        self.scroll_widget = scroll_widget
        self.contents_widget = contents_widget
        self.toggle_button = toggle_button
        self.name_widget = name
        self.documentation = documentation
        self.path = path
        self.records = records

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(scroll_widget)
        self.setLayout(main_layout)

        self.toggle_button.clicked.connect(self.toggle_me)

    def trim(self, docstring):
        if not docstring:
            return ''
        # Convert tabs to spaces (following the normal Python rules)
        # and split into a list of lines:
        lines = docstring.expandtabs().splitlines()
        # Determine minimum indentation (first line doesn't count):
        try:
            indent = sys.maxint
            max = sys.maxint
        except Exception:
            indent = sys.maxsize
            max = sys.maxsize

        for line in lines[1:]:
            stripped = line.lstrip()
            if stripped:
                indent = min(indent, len(line) - len(stripped))
        # Remove indentation (first line is special):
        trimmed = [lines[0].strip()]
        if indent < max:
            for line in lines[1:]:
                trimmed.append(line[indent:].rstrip())
        # Strip off trailing and leading blank lines:
        while trimmed and not trimmed[-1]:
            trimmed.pop()
        while trimmed and not trimmed[0]:
            trimmed.pop(0)
        # Return a single string:
        return '\n'.join(trimmed)

    def set_context(self, index):
        item = index.data(Roles.ItemRole)
        if item.type() == model.InstanceType:
            is_plugin = False
            if item.is_context:
                type_indicator = "C"
            else:
                type_indicator = "I"

            check_color_name = "idle"
            publish_states = index.data(Roles.PublishFlagsRole)
            if publish_states & InstanceStates.InProgress:
                check_color_name = "active"

            elif publish_states & InstanceStates.HasError:
                check_color_name = "error"

            elif publish_states & InstanceStates.HasWarning:
                check_color_name = "warning"

            elif publish_states & InstanceStates.HasFinished:
                check_color_name = "ok"

        elif index.data(Roles.TypeRole) == model.PluginType:
            type_indicator = "P"

            is_plugin = True
            doc = index.data(Roles.DocstringRole)
            doc_str = ""
            have_doc = False
            if doc:
                have_doc = True
                doc_str = self.trim(doc)

            check_color_name = "idle"
            publish_states = index.data(Roles.PublishFlagsRole)
            if publish_states & PluginStates.InProgress:
                check_color_name = "active"

            elif publish_states & PluginStates.HasError:
                check_color_name = "error"

            elif publish_states & PluginStates.HasWarning:
                check_color_name = "warning"

            elif publish_states & PluginStates.WasProcessed:
                check_color_name = "ok"

            self.documentation.toggle_content(have_doc)
            doc_label = QtWidgets.QLabel(doc_str)
            doc_label.setWordWrap(True)
            doc_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.documentation.set_content(doc_label)
            path = index.data(Roles.PathModuleRole) or ''

            self.path.toggle_content(path.strip() != '')
            path_label = QtWidgets.QLabel(path)
            path_label.setWordWrap(True)
            path_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.path.set_content(path_label)
        else:
            self.indicator.setText("?")
            self.path.setVisible(False)
            self.documentation.setVisible(False)
            self.records.setVisible(False)
            return

        self.indicator.setText(type_indicator)
        check_color = self.indicator_colors[check_color_name]
        # TODO do through stylesheets
        self.indicator.setStyleSheet((
            "font-size: 16pt;"
            "font-style: bold;"
            "font-weight: 50;"
            "padding: 5px;"
            "background: {};color: {}"
        ).format(check_color["bg"], check_color["font"]))

        label = index.data(QtCore.Qt.DisplayRole)
        self.name_widget.setText(label)

        self.path.setVisible(is_plugin)
        self.documentation.setVisible(is_plugin)
        self.records.setVisible(True)

        records = index.data(Roles.LogRecordsRole) or []

        len_records = 0
        if records:
            len_records += len(records)

        rec_delegate = delegate.LogsAndDetails()
        rec_view = TerminalView()
        rec_view.setItemDelegate(rec_delegate)

        rec_model = model.Terminal()

        rec_proxy = model.TerminalProxy()
        rec_proxy.setSourceModel(rec_model)

        rec_view.setModel(rec_proxy)

        data = {"records": records}
        rec_model.update_with_result(data)
        rec_proxy.rebuild()

        self.records.button_toggle.setText(
            "{} ({})".format(self.l_rec, len_records)
        )
        self.records.set_content(rec_view)
        self.records.toggle_content(len_records > 0)

    def toggle_me(self):
        self.parent_widget.toggle_perspective_widget()


class ExpandableWidget(QtWidgets.QWidget):

    content = None

    def __init__(self, parent, title):
        super(ExpandableWidget, self).__init__(parent)
        button_size = QtCore.QSize(5, 5)
        button_toggle = QtWidgets.QToolButton()

        button_toggle.setIconSize(button_size)
        button_toggle.setStyleSheet("border: none; background: none;")
        button_toggle.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        button_toggle.setArrowType(QtCore.Qt.RightArrow)
        button_toggle.setText(str(title))
        button_toggle.setCheckable(True)
        button_toggle.setChecked(False)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(9, 9, 9, 0)

        content = QtWidgets.QFrame(self)
        content.setStyleSheet(
            'border: none; background-color: #232323; color:#eeeeee;'
        )
        content.setVisible(False)

        content_layout = QtWidgets.QVBoxLayout(content)

        main_layout.addWidget(button_toggle)
        main_layout.addWidget(content)
        self.setLayout(main_layout)

        self.button_toggle = button_toggle
        self.content_widget = content
        self.content_layout = content_layout
        self.button_toggle.clicked.connect(self.toggle_content)

    def toggle_content(self, *args):
        if len(args) > 0:
            checked = args[0]
        else:
            checked = self.button_toggle.isChecked()
        arrow_type = QtCore.Qt.RightArrow
        if checked:
            arrow_type = QtCore.Qt.DownArrow
        self.button_toggle.setChecked(checked)
        self.button_toggle.setArrowType(arrow_type)
        self.content_widget.setVisible(checked)

    def set_content(self, in_widget):
        if self.content:
            self.content.hide()
            self.content_layout.removeWidget(self.content)
        self.content_layout.addWidget(in_widget)
        self.content = in_widget


class ButtonWithMenu(QtWidgets.QWidget):
    def __init__(self, button_title, parent=None):
        super(ButtonWithMenu, self).__init__(parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
        ))

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.menu = QtWidgets.QMenu()
        self.menu.setStyleSheet("""
            *{color: #fff; background-color: #555; border: 1px solid #222;}
            ::item {background-color: transparent;padding: 5px;
            padding-left: 10px;padding-right: 10px;}
            ::item:selected {background-color: #666;}
        """)

        self.button = QtWidgets.QPushButton(button_title)
        self.button.setObjectName("ButtonWithMenu")

        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.btn_clicked)

    def btn_clicked(self):
        self.menu.popup(self.button.mapToGlobal(
            QtCore.QPoint(0, self.button.height())
        ))

    def addItem(self, text, callback):
        self.menu.addAction(text, callback)
        self.button.setToolTip("Select to apply predefined presets")

    def clearMenu(self):
        self.menu.clear()
        self.button.setToolTip("Presets not found")


class CommentBox(QtWidgets.QLineEdit):

    def __init__(self, placeholder_text, parent=None):
        super(CommentBox, self).__init__(parent=parent)
        self.placeholder = QtWidgets.QLabel(placeholder_text, self)
        self.placeholder.move(2, 2)

    def focusInEvent(self, event):
        self.placeholder.setVisible(False)
        return super(CommentBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        current_text = self.text()
        current_text = current_text.strip(" ")
        self.setText(current_text)
        if not self.text():
            self.placeholder.setVisible(True)
        return super(CommentBox, self).focusOutEvent(event)
