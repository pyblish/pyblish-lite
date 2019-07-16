from .vendor.Qt import QtCore, QtWidgets, QtGui
from . import model, delegate
import traceback


class Item(QtWidgets.QListView):
    # An item is requesting to be toggled, with optional forced-state
    toggled = QtCore.Signal("QModelIndex", object)
    show_perspective = QtCore.Signal("QModelIndex")
    # An item is requesting details
    inspected = QtCore.Signal("QModelIndex")

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

    def leaveEvent(self, event):
        self._inspecting = False
        super(Item, self).leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            self.inspected.emit(index) if index.isValid() else None

        return super(Item, self).mousePressEvent(event)

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


class TerminalView(QtWidgets.QTreeView):
    # An item is requesting to be toggled, with optional forced-state
    toggled = QtCore.Signal("QModelIndex", object)

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
        group = index.data(model.GroupObject)
        if group:
            group.setIsExpanded(self.isExpanded(index))

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

    def leaveEvent(self, event):
        self._inspecting = False
        super(TerminalView, self).leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            indexes = self.selectionModel().selectedIndexes()
            if len(indexes) == 1:
                index = indexes[0]
                if index.data(model.GroupObject):
                    if self.isExpanded(index):
                        self.collapse(index)
                    else:
                        self.expand(index)

            # Deselect all group labels
            if len(indexes) > 0:
                for index in indexes:
                    if index.data(model.GroupObject):
                        self.selectionModel().select(
                            index, QtCore.QItemSelectionModel.Deselect
                        )

        return super(TerminalView, self).mouseReleaseEvent(event)

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


class Details(QtWidgets.QDialog):
    """Popup dialog with detailed information
     _____________________________________
    |                                     |
    | Header                    Timestamp |
    | Subheading                          |
    |                                     |
    |-------------------------------------|
    |                                     |
    | Text                                |
    |_____________________________________|

    """

    def __init__(self, parent=None):
        super(Details, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Popup)
        self.setEnabled(False)
        self.setFixedWidth(100)

        header = QtWidgets.QWidget()

        icon = QtWidgets.QLabel()
        heading = QtWidgets.QLabel()
        subheading = QtWidgets.QLabel()
        timestamp = QtWidgets.QLabel()
        timestamp.setFixedWidth(50)

        layout = QtWidgets.QGridLayout(header)
        layout.addWidget(icon, 0, 0)
        layout.addWidget(heading, 0, 1)
        layout.addWidget(timestamp, 0, 2)
        layout.addWidget(subheading, 1, 1, 1, -1)
        layout.setColumnStretch(1, 1)
        layout.setContentsMargins(5, 5, 5, 5)

        body = QtWidgets.QWidget()

        text = QtWidgets.QLabel()
        text.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(body)
        layout.addWidget(text)
        layout.setContentsMargins(5, 5, 5, 5)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for widget in (header,
                       body):
            widget.setAttribute(QtCore.Qt.WA_StyledBackground)

        names = {
            # Main
            "Icon": icon,
            "Header": header,

            "Heading": heading,
            "Subheading": subheading,
            "Timestamp": timestamp,

            "Body": body,
            "Text": text,
        }

        for name, widget in names.items():
            widget.setObjectName(name)

    def show(self, data):
        # Open before initializing; this allows the widget to properly
        # size itself before filling it with content. The content can
        # then elide itself properly.

        for widget, key in {"Icon": "icon",
                            "Heading": "heading",
                            "Subheading": "subheading",
                            "Timestamp": "timestamp",
                            "Text": "text"}.items():
            widget = self.findChild(QtWidgets.QWidget, widget)
            value = data.get(key, "")

            if key != "text":
                value = widget.fontMetrics().elidedText(value,
                                                        QtCore.Qt.ElideRight,
                                                        widget.width())
            widget.setText(value)
            widget.updateGeometry()

        self.updateGeometry()
        self.setVisible(True)


class PerspectiveWidget(QtWidgets.QWidget):
    l_doc = '   Documentation'
    l_er = '   Error'
    l_trc = '   Traceback'
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
        "warning": {
            "bg": "#cc4a4a",
            "font": "#ffffff"
        },
        "ok": {
            "bg": "#69a567",
            "font": "#ffffff"
        }
    }

    def __init__(self, parent):
        super(PerspectiveWidget, self).__init__(parent)
        # self.setStyleSheet("border:1px solid rgb(0, 255, 0); ")
        self.parent_widget = parent
        main_layout = QtWidgets.QVBoxLayout(self)

        header_widget = QtWidgets.QWidget()
        toggle_button = QtWidgets.QToolButton(header_widget)
        toggle_button.setMinimumHeight(50)

        font = toggle_button.font()
        font.setFamily('FontAwesome')
        font.setPointSize(26)
        toggle_button.setFont(font)
        toggle_button.setText(delegate.icons["angle-left"])
        toggle_button.setStyleSheet(
            "border-bottom: 3px solid lightblue;"
            "border-top: 0px;"
            "border-right: 1px solid #232323;"
            "border-left: 0px;"
        )
        toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        indicator = QtWidgets.QLabel('', parent=header_widget)
        indicator.setMinimumWidth(12)

        name = QtWidgets.QLabel('*Name of inspected', parent=header_widget)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(50)
        font.setKerning(True)
        name.setFont(font)

        indicator.setFont(font)

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
        layout.setContentsMargins(0,0,0,0)

        documentation = ExpandableWidget(self, self.l_doc)
        layout.addWidget(documentation, alignment=QtCore.Qt.AlignTop)

        records = ExpandableWidget(self, self.l_rec)
        layout.addWidget(records, alignment=QtCore.Qt.AlignTop)

        error = ExpandableWidget(self, self.l_er)
        layout.addWidget(error, alignment=QtCore.Qt.AlignTop)

        traceback_part = ExpandableWidget(self, self.l_trc)
        layout.addWidget(traceback_part, alignment=QtCore.Qt.AlignTop)

        path = ExpandableWidget(self, self.l_path)
        layout.addWidget(path, alignment=QtCore.Qt.AlignTop)

        scroll_widget = QtWidgets.QScrollArea(self)
        contents_widget = QtWidgets.QWidget(scroll_widget)
        contents_widget.setLayout(layout)
        contents_widget.setStyleSheet(
            'padding: 0px;'
            'background: "#444";'
        )
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setWidget(contents_widget)

        self.indicator = indicator
        self.scroll_widget = scroll_widget
        self.contents_widget = contents_widget
        self.toggle_button = toggle_button
        self.name_widget = name
        self.documentation = documentation
        self.records = records
        self.error = error
        self.traceback_part = traceback_part
        self.path = path

        main_layout.setContentsMargins(0,0,0,0)
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
        models = self.parent_widget.data['models']
        doc = None
        if index.data(model.Type) == "instance":
            self.indicator.setText('I')
            is_plugin = False
        elif index.data(model.Type) == "plugin":
            self.indicator.setText('P')
            is_plugin = True
            doc = index.data(model.Docstring)
            doc_str = ''
            have_doc = False
            if doc:
                have_doc = True
                doc_str = self.trim(doc)
            self.documentation.toggle_content(have_doc)
            doc_label = QtWidgets.QLabel(doc_str)
            doc_label.setWordWrap(True)
            doc_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.documentation.set_content(doc_label)
            path = index.data(model.PathModule) or ''

            self.path.toggle_content(path.strip() != '')
            path_label = QtWidgets.QLabel(path)
            path_label.setWordWrap(True)
            path_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.path.set_content(path_label)
        else:
            return

        check_color = self.indicator_colors["idle"]
        if index.data(model.IsProcessing) is True:
            check_color = self.indicator_colors["active"]
        elif index.data(model.HasFailed) is True:
            check_color = self.indicator_colors["warning"]
        elif index.data(model.HasSucceeded) is True:
            check_color = self.indicator_colors["ok"]
        elif index.data(model.HasProcessed) is True:
            check_color = self.indicator_colors["ok"]
        self.indicator.setStyleSheet(
            'padding: 5px;'
            'background: {};color: {}'.format(
                check_color['bg'], check_color['font']
            )
        )

        label = index.data(model.Label)
        self.name_widget.setText(label)

        self.path.setVisible(is_plugin)
        self.documentation.setVisible(is_plugin)

        records = index.data(model.LogRecord) or []
        error = index.data(model.ErrorRecord)

        len_records = 0
        if records:
            len_records += len(records)
        if error:
            error_msg = error['message']
            error_fname = error['fname']
            error_line_no = error['line_no']
            error_func = error['func']
            error_traceback = error['traceback']
            len_records += 1

        rec_delegate = delegate.LogsAndDetails()
        rec_view = TerminalView()
        rec_view.setItemDelegate(rec_delegate)

        rec_model = model.Terminal()

        rec_proxy = model.TerminalProxy()
        rec_proxy.setSourceModel(rec_model)

        rec_view.setModel(rec_proxy)

        data = {
            'records': records,
            'error': error
        }
        rec_model.update_with_result(data)
        rec_proxy.rebuild()

        self.records.button_toggle.setText(
            '{} ({})'.format(self.l_rec, len_records)
        )
        self.records.set_content(rec_view)
        self.records.toggle_content(len_records > 0)

        trc_lines = []
        existence_error = False
        error_cnt = ''
        if error:
            existence_error = True
            error_cnt += '<b>Message</b><br/>{}<br/>'.format(
                error_msg.replace('\n','<br/>')
            )
            error_cnt += '<b>Filename</b><br/>{}<br/>'.format(error_fname)
            error_cnt += '<b>Line</b><br/>{}<br/>'.format(error_line_no)
            error_cnt += '<b>Function</b><br/>{}<br/>'.format(error_func)

            trc_widget = QtWidgets.QLabel(''.join(error_traceback))
            trc_widget.setWordWrap(True)
            trc_widget.setTextFormat(QtCore.Qt.PlainText)
            trc_widget.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.traceback_part.set_content(trc_widget)
            isTraceback = True
            if not error_traceback:
                isTraceback = False
            self.traceback_part.setVisible(isTraceback)

        er_widget = QtWidgets.QLabel(error_cnt)
        er_widget.setWordWrap(True)
        er_widget.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.error.set_content(er_widget)

        self.error.toggle_content(existence_error)

        self.traceback_part.toggle_content(False)
        self.traceback_part.setVisible(existence_error)

    def toggle_me(self):
        self.parent_widget.toggle_perspective_widget()


class ExpandableWidget(QtWidgets.QWidget):
    maximum_policy = QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Preferred,
        QtWidgets.QSizePolicy.Maximum
    )
    content = None

    def __init__(self, parent, title):
        super(ExpandableWidget, self).__init__(parent)
        self.setSizePolicy(self.maximum_policy)
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

        content = QtWidgets.QFrame(self)
        content.setVisible(False)
        content.setMinimumHeight(20)
        content.setStyleSheet('background-color: #232323; color:#eeeeee;')

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
