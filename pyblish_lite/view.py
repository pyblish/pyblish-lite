from .vendor.Qt import QtCore, QtWidgets, QtGui
from . import model, delegate


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


class LogView(QtWidgets.QListView):

    # An item is requesting details
    inspected = QtCore.Signal("QModelIndex")

    def __init__(self, parent=None):
        super(LogView, self).__init__(parent)

        self.horizontalScrollBar().hide()
        self.viewport().setAttribute(QtCore.Qt.WA_Hover, True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSelectionMode(QtWidgets.QListView.ExtendedSelection)
        self.setVerticalScrollMode(QtWidgets.QListView.ScrollPerPixel)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            self.inspected.emit(index) if index.isValid() else None

        return super(LogView, self).mousePressEvent(event)

    def rowsInserted(self, parent, start, end):
        """Automatically scroll to bottom on each new item added

        Arguments:
            parent (QtCore.QModelIndex): The model itself, since this is a list
            start (int): Start index of item
            end (int): End index of item

        """

        super(LogView, self).rowsInserted(parent, start, end)

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
    l_rec = '   Records'
    l_path = '   Path'

    def __init__(self, parent):
        super(PerspectiveWidget, self).__init__(parent)
        # self.setStyleSheet("border:1px solid rgb(0, 255, 0); ")
        self.parent_widget = parent
        main_layout = QtWidgets.QVBoxLayout(self)

        toggleButton = QtWidgets.QToolButton()
        font = toggleButton.font()
        font.setPointSize(26)
        toggleButton.setFont(font)
        toggleButton.setText(delegate.icons["angle-left"])
        toggleButton.setStyleSheet(
            "border-bottom: 2px solid #232323;"
            "border-top: 0px;"
            "border-right: 2px solid #232323;"
            "border-left: 0px;"
        )
        toggleButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        name = QtWidgets.QLabel('*Name of inspected')
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(50)
        font.setKerning(True)
        name.setFont(font)

        top_layout = QtWidgets.QHBoxLayout(self)
        top_layout.setAlignment(QtCore.Qt.AlignLeft)
        top_layout.addWidget(toggleButton)
        top_layout.addWidget(name)

        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.addLayout(top_layout)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(0,0,0,0)

        documentation = ExpandableWidget(self, self.l_doc)
        layout.addWidget(documentation)

        records = ExpandableWidget(self, self.l_rec)
        layout.addWidget(records)

        error = ExpandableWidget(self, self.l_er)
        layout.addWidget(error)

        path = ExpandableWidget(self, self.l_path)
        layout.addWidget(path)

        self.toggleButton = toggleButton
        self.name_widget = name
        self.documentation = documentation
        self.records = records
        self.error = error
        self.path = path

        main_layout.addLayout(layout)
        self.setLayout(main_layout)

        self.toggleButton.clicked.connect(self.toggle_me)

    def set_context(self, index):
        models = self.parent_widget.data['models']
        doc = None
        if index.data(model.Type) == "instance":
            cur_model = models['instances']
            is_plugin = False
        elif index.data(model.Type) == "plugin":
            cur_model = models['plugins']
            doc = cur_model.data(index, model.Docstring)
            doc_str = ''
            is_doc = False
            if doc:
                is_doc = True
                doc_str = doc
            self.documentation.toggle_content(is_doc)
            doc_label = QtWidgets.QLabel(doc_str)
            doc_label.setWordWrap(True)
            doc_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.documentation.set_content(doc_label)
            is_plugin = True
        else:
            return

        label = cur_model.data(index, model.Label)
        self.name_widget.setText(label)

        self.path.setVisible(is_plugin)
        self.documentation.setVisible(is_plugin)

        records = cur_model.data(index, model.LogRecord) or []
        error = cur_model.data(index, model.ErrorRecord)

        rec_widget = LogView(self.records.content_widget)
        rec_delegate = delegate.Terminal()
        rec_model = model.Terminal()
        data = {
            'records': records,
            'error': error
        }
        len_records = 0
        if records:
            len_records += len(records)
        if error:
            len_records += 1
        rec_model.update_with_result(data)
        rec_widget.setItemDelegate(rec_delegate)
        rec_widget.setModel(rec_model)
        self.records.button_toggle.setText(
            '{} ({})'.format(self.l_rec, len_records)
        )
        self.records.set_content(rec_widget)
        self.records.toggle_content(len_records > 0)

        error_msg = ''
        if not error:
            existence_error = False
        else:
            existence_error = True
            fname, line_no, func, exc = error.traceback

            error_msg += '<b>Message:</b> {} <br/>'.format(
                exc.replace('\n','<br/>')
            )
            error_msg += '<b>Filename:</b> {} <br/>'.format(fname)
            error_msg += '<b>Line:</b> {} <br/>'.format(line_no)
            error_msg += '<b>Function:</b> {} <br/>'.format(func)

        er_widget = QtWidgets.QLabel(error_msg)
        er_widget.setWordWrap(True)
        er_widget.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.error.set_content(er_widget)
        self.error.toggle_content(existence_error)

    def toggle_me(self):
        self.parent_widget.toggle_perspective_widget()


class ExpandableWidget(QtWidgets.QWidget):
    maximum_policy = QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Preferred,
        QtWidgets.QSizePolicy.Maximum
    )
    content = None

    def __init__(self, parent, title):
        super().__init__(parent)
        self.setSizePolicy(self.maximum_policy)
        button_size = QtCore.QSize(5, 5)
        button_toggle = QtWidgets.QToolButton()

        button_toggle.setIconSize(button_size)
        button_toggle.setStyleSheet("QToolButton { border: none; }")
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

    def toggle_content(self, checked):
        arrow_type = QtCore.Qt.RightArrow
        if checked:
            arrow_type = QtCore.Qt.DownArrow
        self.button_toggle.setChecked(checked)
        self.button_toggle.setArrowType(arrow_type)
        self.content_widget.setVisible(checked)

    def set_content(self, in_widget):
        if self.content:
            self.content_layout.removeWidget(self.content)
        self.content_layout.addWidget(in_widget)
        self.content = in_widget
