"""Per-instance settings widgets for the Artist page."""

from . import model
from .vendor.Qt import QtCore, QtWidgets


def _read_only_label(text):
    label = QtWidgets.QLabel(text or "")
    label.setObjectName("InstanceValue")
    label.setWordWrap(True)
    label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    return label


class InstanceWidget(QtWidgets.QWidget):
    """Form panel for a single publish instance."""

    publish_changed = QtCore.Signal(object, bool)

    def __init__(self, instance, instance_model=None, parent=None):
        super(InstanceWidget, self).__init__(parent)
        self.instance = instance
        self.instance_model = instance_model
        self.setObjectName("InstanceWidget")

        data = instance.data
        title = data.get("label") or data.get("name", "")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.group = QtWidgets.QGroupBox(title)
        self.group.setObjectName("InstanceGroup")
        self.group.setCheckable(True)
        self.group.setChecked(data.get("publish", True))
        self.group.toggled.connect(self._on_publish_toggled)

        group_layout = QtWidgets.QVBoxLayout(self.group)
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(6)

        form = QtWidgets.QFormLayout()
        form.setSpacing(4)
        form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        form.addRow("Asset Type:", _read_only_label(data.get("asset_type")))
        form.addRow("Entity Name:", _read_only_label(data.get("entity_name")))
        form.addRow("Asset Name:", _read_only_label(data.get("asset_name")))
        form.addRow("Entity Variant:", _read_only_label(data.get("entity_variant")))
        form.addRow(
            "LOD Template Path:",
            _read_only_label(data.get("lod_template_path")),
        )

        self.override_shape = QtWidgets.QCheckBox()
        self.override_shape.setChecked(
            data.get("override_shape_attributes", False)
        )
        self.override_shape.toggled.connect(self._on_override_toggled)
        form.addRow("Override shape attributes:", self.override_shape)

        self.comment = QtWidgets.QLineEdit()
        self.comment.setPlaceholderText("Comment")
        self.comment.setText(data.get("comment", ""))
        self.comment.textChanged.connect(self._on_comment_changed)
        form.addRow("Comment:", self.comment)

        group_layout.addLayout(form)
        layout.addWidget(self.group)

    def _sync_model_publish(self, checked):
        if self.instance_model is None:
            return

        try:
            row = self.instance_model.items.index(self.instance)
        except ValueError:
            return

        index = self.instance_model.createIndex(row, 0)
        self.instance_model.setData(index, checked, model.IsChecked)

    def _on_publish_toggled(self, checked):
        self.instance.data["publish"] = checked
        self._sync_model_publish(checked)
        self.publish_changed.emit(self.instance, checked)

    def _on_override_toggled(self, checked):
        self.instance.data["override_shape_attributes"] = checked

    def _on_comment_changed(self, text):
        self.instance.data["comment"] = text


class ArtistInstancesPanel(QtWidgets.QWidget):
    """Scrollable list of instance setting panels for the Artist page."""

    publish_changed = QtCore.Signal(object, bool)

    def __init__(self, parent=None):
        super(ArtistInstancesPanel, self).__init__(parent)
        self.setObjectName("ArtistInstancesPanel")
        self.instance_model = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAsNeeded
        )
        self.scroll_area.setObjectName("ArtistInstancesScroll")

        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_widget.setObjectName("Body")
        self.instances_layout = QtWidgets.QVBoxLayout(self.scroll_widget)
        self.instances_layout.setContentsMargins(0, 0, 0, 0)
        self.instances_layout.setSpacing(8)

        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

    def set_instance_model(self, instance_model):
        self.instance_model = instance_model

    def clear(self):
        while self.instances_layout.count():
            item = self.instances_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh(self, instances):
        """Rebuild instance widgets from the given instances."""
        self.clear()

        if not instances:
            empty = QtWidgets.QLabel("No instances available.")
            empty.setObjectName("Body")
            empty.setAlignment(QtCore.Qt.AlignCenter)
            self.instances_layout.addWidget(empty)
            self.instances_layout.addStretch()
            return

        for instance in instances:
            widget = InstanceWidget(
                instance,
                instance_model=self.instance_model,
                parent=self.scroll_widget,
            )
            widget.publish_changed.connect(self.publish_changed.emit)
            self.instances_layout.addWidget(widget)

        self.instances_layout.addStretch()
