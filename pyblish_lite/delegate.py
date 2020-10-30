import platform

from .vendor.Qt import QtWidgets, QtGui, QtCore

from . import model
from .awesome import tags as awesome

colors = {
    "failed": QtGui.QColor("#ff4a4a"),
    "ok": QtGui.QColor("#77AE24"),
    "active": QtGui.QColor("#99CEEE"),
    "idle": QtCore.Qt.white,
    "font": QtGui.QColor("#DDD"),
    "inactive": QtGui.QColor("#888"),
    "hover": QtGui.QColor(255, 255, 255, 10),
    "selected": QtGui.QColor(255, 255, 255, 20),
    "outline": QtGui.QColor("#333"),
    "warning": QtGui.QColor("#ffa700"),
}

record_colors = {
    "DEBUG": QtGui.QColor("#ff66e8"),
    "INFO": QtGui.QColor("#66abff"),
    "WARNING": QtGui.QColor("#ffba66"),
    "ERROR": QtGui.QColor("#ff4d58"),
    "CRITICAL": QtGui.QColor("#ff4f75"),
}

scale_factors = {"darwin": 1.5}
scale_factor = scale_factors.get(platform.system().lower(), 1.0)
fonts = {
    "h3": QtGui.QFont("Open Sans", 10 * scale_factor, 900),
    "h4": QtGui.QFont("Open Sans", 8 * scale_factor, 400),
    "h5": QtGui.QFont("Open Sans", 8 * scale_factor, 800),
    "smallAwesome": QtGui.QFont("FontAwesome", 8 * scale_factor),
    "largeAwesome": QtGui.QFont("FontAwesome", 16 * scale_factor),
}

icons = {
    "info": awesome["info"],
    "record": awesome["circle"],
    "file": awesome["file"],
    "error": awesome["exclamation-triangle"],
    "action": awesome["adn"],
}


class DPIStyledItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(DPIStyledItemDelegate, self).__init__(*args, **kwargs)
        self._dpi_scale = 1.0

    def set_dpi_scale(self, scale):
        self._dpi_scale = scale


class Item(DPIStyledItemDelegate):
    """Generic delegate for model items"""

    def paint(self, painter, option, index):
        """Paint checkbox and text
         _
        |_|  My label

        """

        body_rect = QtCore.QRectF(option.rect)

        check_rect = QtCore.QRectF(body_rect)
        check_rect.setWidth(check_rect.height())
        buffer = 6 * self._dpi_scale
        check_rect.adjust(buffer, buffer, -buffer, -buffer)

        check_color = colors["idle"]

        if index.data(model.IsProcessing) is True:
            check_color = colors["active"]

        elif index.data(model.HasFailed) is True:
            check_color = colors["failed"]

        elif index.data(model.HasWarning) is True:
            check_color = colors["warning"]

        elif index.data(model.HasSucceeded) is True:
            check_color = colors["ok"]

        elif index.data(model.HasProcessed) is True:
            check_color = colors["ok"]

        # Maintain reference to state, so we can restore it once we're done
        painter.save()
        painter.setFont(fonts["h4"])
        metrics = painter.fontMetrics()

        label_rect = QtCore.QRectF(
            option.rect.adjusted(
                check_rect.width() + 12 * self._dpi_scale,
                2 * self._dpi_scale,
                0,
                -2 * self._dpi_scale,
            )
        )

        assert label_rect.width() > 0

        label = index.data(model.Label)
        label = metrics.elidedText(
            label, QtCore.Qt.ElideRight, label_rect.width() - 20 * self._dpi_scale
        )

        font_color = colors["idle"]
        if not index.data(model.IsChecked):
            font_color = colors["inactive"]

        # Draw label
        painter.setPen(QtGui.QPen(font_color))
        painter.drawText(label_rect, label)

        # Draw action icon
        if index.data(model.ActionIconVisible):
            painter.save()

            if index.data(model.ActionIdle):
                color = colors["idle"]
            elif index.data(model.IsProcessing):
                color = colors["active"]
            elif index.data(model.ActionFailed):
                color = colors["warning"]
            else:
                color = colors["ok"]

            painter.setFont(fonts["smallAwesome"])
            painter.setPen(QtGui.QPen(color))

            icon_rect = QtCore.QRectF(
                option.rect.adjusted(
                    label_rect.width() + 1 * self._dpi_scale,
                    label_rect.height() / (3 * self._dpi_scale),
                    0,
                    0,
                )
            )
            painter.drawText(icon_rect, icons["action"])

            painter.restore()

        # Draw checkbox
        pen = QtGui.QPen(check_color, 1)
        painter.setPen(pen)

        if index.data(model.IsOptional):
            painter.drawRect(check_rect)

            if index.data(model.IsChecked):
                painter.fillRect(check_rect, check_color)

        elif not index.data(model.IsIdle) and index.data(model.IsChecked):
            painter.fillRect(check_rect, check_color)

        if option.state & QtWidgets.QStyle.State_MouseOver:
            painter.fillRect(body_rect, colors["hover"])

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(body_rect, colors["selected"])

        # Ok, we're done, tidy up.
        painter.restore()

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), 20 * self._dpi_scale)


class Artist(DPIStyledItemDelegate):
    """Delegate used on Artist page"""

    def paint(self, painter, option, index):
        """Paint checkbox and text

         _________________________________________
        |       |  label              | duration  |
        |toggle |_____________________|           |
        |       |  families           |           |
        |_______|_____________________|___________|

        """
        # Maintain reference to state, so we can restore it once we're done
        painter.save()

        # Layout
        spacing = 10 * self._dpi_scale

        body_rect = QtCore.QRectF(option.rect).adjusted(
            2 * self._dpi_scale,
            2 * self._dpi_scale,
            -8 * self._dpi_scale,
            -2 * self._dpi_scale,
        )
        buffer = 5 * self._dpi_scale
        content_rect = body_rect.adjusted(buffer, buffer, -buffer, -buffer)

        toggle_rect = QtCore.QRectF(body_rect)
        toggle_rect.setWidth(7 * self._dpi_scale)
        toggle_rect.adjust(
            1 * self._dpi_scale, 1 * self._dpi_scale, 0, -1 * self._dpi_scale
        )

        icon_rect = QtCore.QRectF(content_rect)
        icon_rect.translate(toggle_rect.width() + spacing, 3 * self._dpi_scale)
        icon_rect.setWidth(35 * self._dpi_scale)
        icon_rect.setHeight(35 * self._dpi_scale)

        duration_rect = QtCore.QRectF(content_rect)
        duration_rect.translate(content_rect.width() - 50, 0)

        label_font = fonts["h3"]
        label_metrics = QtGui.QFontMetrics(label_font)
        label_rect = QtCore.QRectF(content_rect)
        label_rect.translate(icon_rect.width() + spacing, 0)
        label_rect.setHeight(label_metrics.lineSpacing() + spacing)

        families_rect = QtCore.QRectF(label_rect)
        families_rect.translate(0, label_rect.height())

        # Colors
        check_color = colors["idle"]

        if index.data(model.IsProcessing) is True:
            check_color = colors["active"]

        elif index.data(model.HasFailed) is True:
            check_color = colors["warning"]

        elif index.data(model.HasSucceeded) is True:
            check_color = colors["ok"]

        elif index.data(model.HasProcessed) is True:
            check_color = colors["ok"]

        icon = index.data(model.Icon) or icons["file"]
        label = index.data(model.Label)
        families = ", ".join(index.data(model.Families))

        # Elide
        label = label_metrics.elidedText(
            label, QtCore.Qt.ElideRight, label_rect.width()
        )

        family_font = fonts["h5"]
        family_metrics = QtGui.QFontMetrics(family_font)
        families = family_metrics.elidedText(
            families, QtCore.Qt.ElideRight, label_rect.width()
        )

        font_color = colors["idle"]
        if not index.data(model.IsChecked):
            font_color = colors["inactive"]

        # Draw background
        painter.fillRect(body_rect, colors["hover"])

        painter.setFont(fonts["largeAwesome"])
        painter.setPen(QtGui.QPen(font_color))
        painter.drawText(icon_rect, icon)

        # Draw label
        painter.setFont(label_font)
        painter.drawText(label_rect, label)

        # Draw families
        painter.setFont(family_font)
        painter.setPen(QtGui.QPen(colors["inactive"]))
        painter.drawText(families_rect, families)

        # Draw checkbox
        pen = QtGui.QPen(check_color, 1)
        painter.setPen(pen)

        if index.data(model.IsOptional):
            painter.drawRect(toggle_rect)

            if index.data(model.IsChecked):
                painter.fillRect(toggle_rect, check_color)

        elif not index.data(model.IsIdle) and index.data(model.IsChecked):
            painter.fillRect(toggle_rect, check_color)

        if option.state & QtWidgets.QStyle.State_MouseOver:
            painter.fillRect(body_rect, colors["hover"])

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(body_rect, colors["selected"])

        painter.setPen(colors["outline"])
        painter.drawRect(body_rect)

        # Ok, we're done, tidy up.
        painter.restore()

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), 80 * self._dpi_scale)


class Terminal(DPIStyledItemDelegate):
    """Delegate used exclusively for the Terminal"""

    def paint(self, painter, option, index):
        """Paint text"""

        buffer = 3 * self._dpi_scale
        icon_rect = QtCore.QRectF(option.rect).adjusted(
            buffer, buffer, -buffer, -buffer
        )
        size = 14 * self._dpi_scale
        icon_rect.setWidth(size)
        icon_rect.setHeight(size)

        icon_color = colors["idle"]
        icon = icons[index.data(model.Type)]

        if index.data(model.Type) == "record":
            icon_color = record_colors[index.data(model.LogLevel)]

        elif index.data(model.Type) == "error":
            icon_color = colors["warning"]

        label_rect = QtCore.QRectF(
            option.rect.adjusted(
                icon_rect.width() + 12 * self._dpi_scale,
                2 * self._dpi_scale,
                0,
                -2 * self._dpi_scale,
            )
        )

        assert label_rect.width() > 0

        label_font = fonts["h4"]
        label_metrics = QtGui.QFontMetrics(label_font)
        label = index.data(model.Label)
        label = label_metrics.elidedText(
            label, QtCore.Qt.ElideRight, label_rect.width() - 20 * self._dpi_scale
        )

        font_color = colors["idle"]

        hover = QtGui.QPainterPath()
        hover.addRect(
            QtCore.QRectF(option.rect).adjusted(
                0, 0, -1 * self._dpi_scale, -1 * self._dpi_scale
            )
        )

        # Maintain reference to state, so we can restore it once we're done
        painter.save()

        # Draw label
        painter.setFont(label_font)
        painter.setPen(QtGui.QPen(font_color))
        painter.drawText(label_rect, label)

        # Draw icon
        painter.setFont(fonts["smallAwesome"])
        painter.setPen(QtGui.QPen(icon_color))
        painter.drawText(icon_rect, QtCore.Qt.AlignCenter, icon)

        if option.state & QtWidgets.QStyle.State_MouseOver:
            painter.fillPath(hover, colors["hover"])

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillPath(hover, colors["selected"])

        # Ok, we're done, tidy up.
        painter.restore()

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), 20 * self._dpi_scale)
