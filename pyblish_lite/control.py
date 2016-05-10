import os
import traceback

from Qt import QtCore, QtWidgets, QtGui

import pyblish.api
import pyblish.util
import pyblish.logic

from . import model, view


class Window(QtWidgets.QDialog):
    finished = QtCore.Signal()

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("Pyblish")
        self.setWindowIcon(QtGui.QIcon("img/logo-extrasmall.png"))

        """General layout
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

        left_view = view.ItemView()
        right_view = view.ItemView()

        delegate = view.CheckBoxDelegate()
        left_view.setItemDelegate(delegate)
        right_view.setItemDelegate(delegate)

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

        instance_model = model.InstanceModel()
        plugin_model = model.PluginModel()

        left_view.setModel(instance_model)
        right_view.setModel(plugin_model)

        """Setup
              ___
             |   |
          /\/     \/\
         /     _     \
         \    / \    /
          |   | |   |
         /    \_/    \
         \           /
          \/\     /\/
             |___|

        """

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
                "is_running": False,
                "is_closing": False,
                "close_requested": False
            }
        }

        # Defaults
        home.setCheckState(QtCore.Qt.Checked)

        """Signals
         ________     ________
        |________|-->|________|
                         |
                         |
                      ___v____
                     |________|

        """

        delegate.toggled.connect(self.on_toggled)
        reset.clicked.connect(self.prepare_reset)
        play.clicked.connect(self.prepare_publish)
        right_view.customContextMenuRequested.connect(
            self.on_plugin_action_menu)

    def on_toggled(self, index):
        """An item is requesting to be toggled"""
        if index.data(model.HasProcessed):
            print("Cannot toggle")
            return

        value = not index.data(model.IsChecked)
        index.model().setData(index, value, model.IsChecked)

    def iterator(self, plugins, context):
        """Primary iterator

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

            if not self.data["state"]["is_running"]:
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

    def prepare_publish(self):
        print("Preparing publish..")

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        defer(5, self.publish)

    def publish(self):
        self.data["state"]["is_running"] = True
        models = self.data["models"]

        plugins = self.data["state"]["plugins"]
        context = self.data["state"]["context"]

        def on_next():
            try:
                result = iterator.next()
                models["plugins"].update_with_result(result)
                models["instances"].update_with_result(result)
                defer(100, on_next)

            except StopIteration as e:
                print(e)
                defer(500, self.finish_publish)

            except Exception as e:
                stack = traceback.format_exc(e)
                defer(500, lambda: self.finish_publish(stack))

        plugins = list(
            p for p in plugins
            if not pyblish.lib.inrange(
                p.order,
                base=pyblish.api.CollectorOrder)
        )

        iterator = self.iterator(plugins, context)
        defer(100, on_next)

    def finish_publish(self, error=None):
        if error is not None:
            print("An error occurred.\n\n%s" % error)

        self.data["state"]["is_running"] = False

        plugin_model = self.data["models"]["plugins"]
        for index in plugin_model:
            plugin_model.setData(index, model.IsIdle, False)

        buttons = self.data["buttons"]
        buttons["reset"].show()
        buttons["stop"].hide()

        self.finished.emit()
        print("Finished")

    def prepare_reset(self):
        print("About to reset..")

        self.data["state"]["context"] = list()
        self.data["state"]["plugins"] = list()

        for m in self.data["models"].values():
            m.reset()

        for b in self.data["buttons"].values():
            b.hide()

        self.data["buttons"]["stop"].show()

        defer(500, self.reset)

    def reset(self):
        """Discover plug-ins and run collection"""
        self.data["state"]["is_running"] = True

        models = self.data["models"]

        plugins = pyblish.api.discover()
        context = pyblish.api.Context()

        models = self.data["models"]

        for Plugin in plugins:
            models["plugins"].append(Plugin)

        def on_next():
            try:
                result = iterator.next()
                models["plugins"].update_with_result(result)
                models["instances"].update_with_result(result)
                defer(100, on_next)

            except StopIteration:
                for instance in context:
                    models["instances"].append(instance)

                defer(500, self.finish_reset)

            except Exception as e:
                stack = traceback.format_exc(e)
                defer(500, lambda: self.finish_reset(stack))

        collectors = list(
            p for p in plugins
            if pyblish.lib.inrange(
                p.order,
                base=pyblish.api.CollectorOrder)
        )

        self.data["state"]["context"] = context
        self.data["state"]["plugins"] = plugins

        iterator = self.iterator(collectors, context)
        defer(100, on_next)

    def finish_reset(self, error=None):
        if error is not None:
            print("An error occurred.\n\n%s" % error)

        print("Finishing up reset..")

        buttons = self.data["buttons"]
        buttons["play"].show()
        buttons["reset"].show()
        buttons["stop"].hide()

        self.data["state"]["is_running"] = False
        self.finished.emit()

    def on_plugin_action_menu(self, pos):
        index = self.data["views"]["right"].indexAt(pos)
        actions = index.data(model.Actions)

        if not actions:
            return

        menu = QtWidgets.QMenu(self)
        plugin = self.data["models"]["plugins"].items[index.row()]

        for action in actions:
            qaction = QtWidgets.QAction(action.label or action.__name__, self)
            qaction.triggered.connect(
                lambda checked, p=plugin, a=action: self.prepare_action(p, a)
            )

            menu.addAction(qaction)

        menu.popup(self.data["views"]["right"].viewport().mapToGlobal(pos))

    def prepare_action(self, plugin, action):
        print("Preparing action..")

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        self.data["state"]["is_running"] = True

        defer(100, lambda: self.run_action(plugin, action))

    def run_action(self, plugin, action):
        models = self.data["models"]
        context = self.data["state"]["context"]

        def on_next():
            result = pyblish.plugin.process(plugin, context, None, action.id)
            models["plugins"].update_with_result(result)
            models["instances"].update_with_result(result)
            defer(500, self.finish_action)

        defer(100, on_next)

    def finish_action(self, error=None):
        if error is not None:
            print("An error occurred.\n\n%s" % error)

        self.data["state"]["is_running"] = False

        buttons = self.data["buttons"]
        buttons["reset"].show()
        buttons["stop"].hide()
        print("Finished")

    def closeEvent(self, event):
        """Perform post-flight checks before closing

        Make sure processing of any kind is wrapped up before closing

        """

        if self.data["state"]["is_closing"]:
            print("Good bye")
            return super(Window, self).closeEvent(event)

        print("Closing..")

        if self.data["state"]["is_running"]:
            print("..as soon as processing is finished..")
            self.data["state"]["is_running"] = False
            self.finished.connect(self.close)
            return event.ignore()

        self.data["state"]["is_closing"] = True

        # Explicitly clear potentially referenced data
        print("Cleaning up..")
        for instance in self.data["state"].get("context", []):
            del(instance)

        for plugin in self.data["state"].get("plugins", []):
            del(plugin)

        defer(200, self.close)
        return event.ignore()


def defer(delay, func):
    """Append artificial delay to `func`

    Arguments:
        delay (float): Delay multiplier; default 1, 0 means no delay
        func (callable): Any callable

    """

    delay *= float(os.getenv("PYBLISH_DELAY", 1))
    if delay > 0:
        return QtCore.QTimer.singleShot(delay, func)
    else:
        return func()
