import platform

from .vendor.Qt import QtWidgets, QtGui, QtCore

from . import model
from .awesome import tags as awesome

colors = {
    "warning": QtGui.QColor("#ff4a4a"),
    "ok": QtGui.QColor("#77AE24"),
    "active": QtGui.QColor("#99CEEE"),
    "idle": QtCore.Qt.white,
    "font": QtGui.QColor("#DDD"),
    "inactive": QtGui.QColor("#888"),
    "hover": QtGui.QColor(255, 255, 255, 10),
    "selected": QtGui.QColor(255, 255, 255, 20),
    "outline": QtGui.QColor("#333"),
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


class Item(QtWidgets.QStyledItemDelegate):
    """Generic delegate for model items"""

    def paint(self, painter, option, index):
        """Paint checkbox and text
         _
        |_|  My label

        """

        body_rect = QtCore.QRectF(option.rect)

        check_rect = QtCore.QRectF(body_rect)
        check_rect.setWidth(check_rect.height())
        check_rect.adjust(6, 6, -6, -6)

        check_color = colors["idle"]

        if index.data(model.IsProcessing) is True:
            check_color = colors["active"]

        elif index.data(model.HasFailed) is True:
            check_color = colors["warning"]

        elif index.data(model.HasSucceeded) is True:
            check_color = colors["ok"]

        elif index.data(model.HasProcessed) is True:
            check_color = colors["ok"]

        metrics = painter.fontMetrics()

        label_rect = QtCore.QRectF(option.rect.adjusted(
            check_rect.width() + 12, 2, 0, -2))

        assert label_rect.width() > 0

        label = index.data(model.Label)
        label = metrics.elidedText(label,
                                   QtCore.Qt.ElideRight,
                                   label_rect.width() - 20)

        font_color = colors["idle"]
        if not index.data(model.IsChecked):
            font_color = colors["inactive"]

        # Maintain reference to state, so we can restore it once we're done
        painter.save()

        # Draw label
        painter.setFont(fonts["h4"])
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

            icon_rect = QtCore.QRectF(option.rect.adjusted(
                label_rect.width() + 1, label_rect.height() / 3, 0, 0))
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
        return QtCore.QSize(option.rect.width(), 20)


class Artist(QtWidgets.QStyledItemDelegate):
    """Delegate used on Artist page"""

    def paint(self, painter, option, index):
        """Paint checkbox and text

         _________________________________________
        |       |  label              | duration  |
        |toggle |_____________________|           |
        |       |  families           |           |
        |_______|_____________________|___________|

        """

        # Layout
        spacing = 10
        metrics = painter.fontMetrics()

        body_rect = QtCore.QRectF(option.rect).adjusted(2, 2, -8, -2)
        content_rect = body_rect.adjusted(5, 5, -5, -5)

        toggle_rect = QtCore.QRectF(body_rect)
        toggle_rect.setWidth(7)
        toggle_rect.adjust(1, 1, 0, -1)

        icon_rect = QtCore.QRectF(content_rect)
        icon_rect.translate(toggle_rect.width() + spacing, 3)
        icon_rect.setWidth(35)
        icon_rect.setHeight(35)

        duration_rect = QtCore.QRectF(content_rect)
        duration_rect.translate(content_rect.width() - 50, 0)

        label_rect = QtCore.QRectF(content_rect)
        label_rect.translate(icon_rect.width() +
                             spacing, 0)
        label_rect.setHeight(metrics.lineSpacing() + spacing)

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
        label = metrics.elidedText(label,
                                   QtCore.Qt.ElideRight,
                                   label_rect.width())

        families = metrics.elidedText(families,
                                      QtCore.Qt.ElideRight,
                                      label_rect.width())

        font_color = colors["idle"]
        if not index.data(model.IsChecked):
            font_color = colors["inactive"]

        # Maintan reference to state, so we can restore it once we're done
        painter.save()

        # Draw background
        painter.fillRect(body_rect, colors["hover"])

        painter.setFont(fonts["largeAwesome"])
        painter.setPen(QtGui.QPen(font_color))
        painter.drawText(icon_rect, icon)

        # Draw label
        painter.setFont(fonts["h3"])
        painter.drawText(label_rect, label)

        # Draw families
        painter.setFont(fonts["h5"])
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
        return QtCore.QSize(option.rect.width(), 80)


class Terminal(QtWidgets.QStyledItemDelegate):
    """Delegate used exclusively for the Terminal"""

    def paint(self, painter, option, index):
        """Paint text"""

        icon_rect = QtCore.QRectF(option.rect).adjusted(3, 3, -3, -3)
        icon_rect.setWidth(14)
        icon_rect.setHeight(14)

        icon_color = colors["idle"]
        icon = icons[index.data(model.Type)]

        if index.data(model.Type) == "record":
            icon_color = record_colors[index.data(model.LogLevel)]

        elif index.data(model.Type) == "error":
            icon_color = colors["warning"]

        metrics = painter.fontMetrics()

        label_rect = QtCore.QRectF(option.rect.adjusted(
            icon_rect.width() + 12, 2, 0, -2))

        assert label_rect.width() > 0

        label = index.data(model.Label)
        label = metrics.elidedText(label,
                                   QtCore.Qt.ElideRight,
                                   label_rect.width() - 20)

        font_color = colors["idle"]

        hover = QtGui.QPainterPath()
        hover.addRect(QtCore.QRectF(option.rect).adjusted(0, 0, -1, -1))

        # Maintain reference to state, so we can restore it once we're done
        painter.save()

        # Draw label
        painter.setFont(fonts["h4"])
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
        return QtCore.QSize(option.rect.width(), 20)
