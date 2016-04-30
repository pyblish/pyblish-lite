from Qt import QtCore, QtWidgets, QtGui

import pyblish.api
import pyblish.util
import pyblish.logic

from . import model, view, util


class Window(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("Pyblish")
        self.setWindowIcon(QtGui.QIcon("img/logo-extrasmall.png"))

        """
         __________________
        |                  |
        |      Header      |
        |__________________|
        |                  |
        |                  |
        |                  |
        |       Body       |
        |                  |
        |                  |
        |                  |
        |__________________|
        |                  |
        |      Footer      |
        |__________________|

        """

        header = QtWidgets.QWidget()

        home = QtWidgets.QCheckBox()
        spacer = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout(header)
        layout.addWidget(home, 0)
        layout.addWidget(spacer, 1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        body = QtWidgets.QWidget()

        left_view = view.TableView()
        right_view = view.TableView()

        layout = QtWidgets.QHBoxLayout(body)
        layout.addWidget(left_view)
        layout.addWidget(right_view)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        # Add some room between window borders and body
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 0)
        layout.addWidget(body)

        footer = QtWidgets.QWidget()
        spacer = QtWidgets.QWidget()
        reset = QtWidgets.QPushButton()
        play = QtWidgets.QPushButton()
        stop = QtWidgets.QPushButton()

        layout = QtWidgets.QHBoxLayout(footer)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(spacer, 1)
        layout.addWidget(reset, 0)
        layout.addWidget(play, 0)
        layout.addWidget(stop, 0)

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(container)
        layout.addWidget(footer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        instance_model = model.TableModel()
        plugin_model = model.TableModel()

        left_view.setModel(instance_model)
        right_view.setModel(plugin_model)

        names = {
            # Main
            "Header": header,
            "Body": body,
            "Container": container,
            "Footer": footer,
            "Home": home,

            # Buttons
            "Play": play,
            "Reset": reset,
            "Stop": stop
        }

        for name, widget in names.items():
            widget.setObjectName(name)

        # Enable CSS on plain QWidget objects
        for widget in (header,
                       body,
                       container,
                       footer,
                       play,
                       stop,
                       reset):
            widget.setAttribute(QtCore.Qt.WA_StyledBackground)

        self.data = {
            "views": {
                "left": left_view,
                "right": right_view
            },
            "models": {
                "instances": instance_model,
                "plugins": plugin_model
            },
            "tabs": {
                "home": home,
            },
            "buttons": {
                "play": play,
                "stop": stop,
                "reset": reset
            },
            "state": {
                "context": list(),
                "plugins": list(),
                "isRunning": False
            }
        }

        self.set_defaults()

        reset.clicked.connect(self.prepare_reset)
        play.clicked.connect(self.prepare_publish)

    def iterator(self, plugins, context):
        """Primary iterator

        CAUTION: THIS RUNS IN A SEPARATE THREAD

        This is the brains of publishing. It handles logic related
        to which plug-in to process with which Instance or Context,
        in addition to stopping when necessary.

        """

        test = pyblish.logic.registered_test()
        state = {
            "nextOrder": None,
            "ordersWithError": set()
        }

        for plug, instance in pyblish.logic.Iterator(plugins, context):
            if not plug.active:
                continue

            state["nextOrder"] = plug.order

            if not self.data["state"]["isRunning"]:
                raise StopIteration("Stopped")

            if test(**state):
                raise StopIteration("Stopped due to %s" % test(**state))

            try:
                # Notify GUI before commencing remote processing
                result = pyblish.plugin.process(plug, context, instance)

            except Exception as e:
                raise StopIteration("Unknown error: %s" % e)

            else:
                # Make note of the order at which the
                # potential error error occured.
                has_error = result["error"] is not None
                if has_error:
                    state["ordersWithError"].add(plug.order)

            yield result

    def set_defaults(self):
        """Initialise elements of the GUI

        TODO: This will quickly get messy.
            Manage this via a statemachine instead.

        """

        tabs = self.data["tabs"]
        tabs["home"].setCheckState(QtCore.Qt.Checked)

    def prepare_publish(self):
        print("Preparing publish..")

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        QtCore.QTimer.singleShot(5, self.publish)

    def publish(self):
        self.data["state"]["isRunning"] = True

        instance_model = self.data["models"]["instances"]
        plugin_model = self.data["models"]["plugins"]

        plugins = self.data["state"]["plugins"]
        context = self.data["state"]["context"]

        def on_next(result):
            if isinstance(result, StopIteration):
                return QtCore.QTimer.singleShot(500, self.finish_publish)

            instance_model.update_with_result(result)
            plugin_model.update_with_result(result)

            util.async(iterator.next, callback=on_next)

        iterator = self.iterator(plugins, context)
        util.async(iterator, callback=on_next)

    def finish_publish(self):
        self.data["state"]["isRunning"] = False

        buttons = self.data["buttons"]
        buttons["reset"].show()
        buttons["stop"].hide()
        print("Finished")

    def prepare_reset(self):
        print("About to reset..")

        for m in self.data["models"].values():
            m.reset()

        for b in self.data["buttons"].values():
            b.hide()

        self.data["buttons"]["stop"].show()
        QtCore.QTimer.singleShot(500, self.reset)

    def reset(self):
        """Discover plug-ins and run collection"""
        plugins = pyblish.api.discover()
        context = pyblish.util.collect(plugins=plugins)

        models = self.data["models"]

        for Plugin in plugins:
            ischecked = Plugin.active

            models["plugins"].append([
                {   # Column 0 - Checkbox
                    QtCore.Qt.EditRole: (
                        QtCore.Qt.Checked if ischecked else
                        QtCore.Qt.Unchecked),
                    model.DataRole: Plugin,
                    model.StateRole: "idle",
                },
                {   # Column 1 - Label
                    QtCore.Qt.DisplayRole: Plugin.__name__,
                },
            ])

        for instance in context:
            ischecked = instance.data.get("publish", True)

            models["instances"].append([
                {   # Column 0
                    QtCore.Qt.EditRole: (
                        QtCore.Qt.Checked if ischecked
                        else QtCore.Qt.Unchecked),
                    model.DataRole: instance,
                    model.StateRole: "idle",
                },
                {   # Column 1
                    QtCore.Qt.DisplayRole: instance.data["name"],
                },
            ])

        self.data["state"]["context"] = context
        self.data["state"]["plugins"] = plugins

        self.finish_reset()

    def finish_reset(self):
        print("Finishing up reset..")

        buttons = self.data["buttons"]
        buttons["play"].show()
        buttons["reset"].show()
        buttons["stop"].hide()
