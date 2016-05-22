from Qt import QtWidgets, QtGui, QtCore

from . import model

colors = {
    "warning": QtGui.QColor("#ff4a4a"),
    "ok": QtGui.QColor("#77AE24"),
    "active": QtGui.QColor("#99CEEE"),
    "idle": QtCore.Qt.white,
    "font": QtGui.QColor("#DDD"),
    "inactive": QtGui.QColor("#888"),
    "hover": QtGui.QColor(255, 255, 255, 10),
    "selected": QtGui.QColor(255, 255, 255, 20),
}

record_colors = {
    "DEBUG": QtGui.QColor("#ff66e8"),
    "INFO": QtGui.QColor("#66abff"),
    "WARNING": QtGui.QColor("#ffba66"),
    "ERROR": QtGui.QColor("#ff4d58"),
    "CRITICAL": QtGui.QColor("#ff4f75"),
}

fonts = {
    "h3": QtGui.QFont("Open Sans", 10, 400),
    "h4": QtGui.QFont("Open Sans", 8, 400),
    "h5": QtGui.QFont("Open Sans", 8, 800),
    "awesome": QtGui.QFont("FontAwesome", 8)
}

icons = {
    "info": u"\uf129",  # fa-info
    "record": u"\uf111",   # fa-circle
    "error": u"\uf071",    # fa-exclamation-triangle
}


class Item(QtWidgets.QStyledItemDelegate):
    """Generic delegate for model items"""

    def paint(self, painter, option, index):
        """Paint checkbox and text
         _
        |_|  My label

        """

        check_rect = QtCore.QRectF(option.rect)
        check_rect.setWidth(check_rect.height())
        check_rect.adjust(6, 6, -6, -6)

        check_path = QtGui.QPainterPath()
        check_path.addRect(check_rect)

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

        hover = QtGui.QPainterPath()
        hover.addRect(QtCore.QRectF(option.rect).adjusted(0, 0, -1, -1))

        # Maintain reference to state, so we can restore it once we're done
        painter.save()

        # Draw label
        painter.setFont(fonts["h4"])
        painter.setPen(QtGui.QPen(font_color))
        painter.drawText(label_rect, label)

        # Draw checkbox
        pen = QtGui.QPen(check_color, 1)
        painter.setPen(pen)

        if index.data(model.IsOptional):
            painter.drawPath(check_path)

            if index.data(model.IsChecked):
                painter.fillPath(check_path, check_color)

        elif not index.data(model.IsIdle) and index.data(model.IsChecked):
                painter.fillPath(check_path, check_color)

        if option.state & QtWidgets.QStyle.State_MouseOver:
            painter.fillPath(hover, colors["hover"])

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillPath(hover, colors["selected"])

        # Ok, we're done, tidy up.
        painter.restore()

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), 20)


class Artist(QtWidgets.QStyledItemDelegate):
    """Delegate used on Artist page"""

    def paint(self, painter, option, index):
        """Paint checkbox and text
         _
        | |  My label
        |_|  My family

        """

        rect = QtCore.QRectF(option.rect)
        rect.setWidth(rect.height())
        rect.adjust(0, 0, -35, 0)

        path = QtGui.QPainterPath()
        path.addRect(rect)

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

        rect = QtCore.QRectF(option.rect.adjusted(rect.width() + 12, 0, 0, -2))
        assert rect.width() > 0

        label = index.data(model.Label)
        label = metrics.elidedText(label,
                                   QtCore.Qt.ElideRight,
                                   rect.width())

        families = ", ".join(index.data(model.Families))
        families = metrics.elidedText(families,
                                      QtCore.Qt.ElideRight,
                                      rect.width())

        font_color = colors["idle"]
        if not index.data(model.IsChecked):
            font_color = colors["inactive"]

        hover = QtGui.QPainterPath()
        hover.addRect(QtCore.QRectF(option.rect).adjusted(0, 0, -1, -1))

        # Maintan reference to state, so we can restore it once we're done
        painter.save()

        # Draw label
        painter.setFont(fonts["h3"])
        painter.setPen(QtGui.QPen(font_color))
        painter.drawText(rect, label)

        rect = QtCore.QRectF(option.rect.adjusted(17, 18, 0, -2))

        # Draw families
        painter.setFont(fonts["h5"])
        painter.setPen(QtGui.QPen(colors["inactive"]))
        painter.drawText(rect, families)

        # Draw checkbox
        pen = QtGui.QPen(check_color, 1)
        painter.setPen(pen)

        if index.data(model.IsOptional):
            painter.drawPath(path)

            if index.data(model.IsChecked):
                painter.fillPath(path, check_color)

        elif not index.data(model.IsIdle) and index.data(model.IsChecked):
                painter.fillPath(path, check_color)

        if option.state & QtWidgets.QStyle.State_MouseOver:
            painter.fillPath(hover, colors["hover"])

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillPath(hover, colors["selected"])

        # Ok, we're done, tidy up.
        painter.restore()

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), 40)


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

        if index.data(model.Expanded):
            painter.setPen(colors["inactive"])
            y = metrics.height()

            for key, value in index.data(model.Data).items():
                if key.startswith("_"):
                    continue

                painter.drawText(label_rect.adjusted(0, y, 0, y),
                                 "%s = %s" % (key, value))
                y += metrics.height()

        # Draw icon
        painter.setFont(fonts["awesome"])
        painter.setPen(QtGui.QPen(icon_color))
        painter.drawText(icon_rect, QtCore.Qt.AlignCenter, icon)

        if option.state & QtWidgets.QStyle.State_MouseOver:
            painter.fillPath(hover, colors["hover"])

        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillPath(hover, colors["selected"])

        # Ok, we're done, tidy up.
        painter.restore()

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(),
                            180 if index.data(model.Expanded) else 20)
