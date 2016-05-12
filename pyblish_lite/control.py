import os
import traceback

from Qt import QtCore, QtWidgets, QtGui

import pyblish.api
import pyblish.util
import pyblish.logic

from . import model, view, util


class Window(QtWidgets.QDialog):
    # Emitted when the GUI is about to start processing;
    # e.g. resetting, validating or publishing.
    about_to_process = QtCore.Signal(object, object)

    # Emitted when processing has finished
    finished = QtCore.Signal()

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("Pyblish")
        self.setWindowIcon(QtGui.QIcon(
            util.get_asset("img", "logo-extrasmall.png"))
        )

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

        for v in (left_view, right_view):
            mode = QtWidgets.QAbstractItemView.ExtendedSelection
            v.setSelectionMode(mode)

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

        # Placeholder for when GUI is closing
        closing_placeholder = QtWidgets.QWidget()
        closing_placeholder.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                          QtWidgets.QSizePolicy.Expanding)
        closing_placeholder.hide()
        layout.addWidget(closing_placeholder, 0)

        footer = QtWidgets.QWidget()
        info = QtWidgets.QLabel()
        spacer = QtWidgets.QWidget()
        reset = QtWidgets.QPushButton(u"\uf021")  # fa-refresh
        play = QtWidgets.QPushButton(u"\uf04b")   # fa-play
        stop = QtWidgets.QPushButton(u"\uf04d")   # fa-stop

        layout = QtWidgets.QHBoxLayout(footer)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(info, 0)
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
            "Info": info,

            # Buttons
            "Play": play,
            "Reset": reset,
            "Stop": stop,

            # Misc
            "ClosingPlaceholder": closing_placeholder,
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
                # These are internal caches of the data
                # visualised by the model. The model then
                # modified these objects as-is, such as their
                # "active" attribute or "publish" data.
                "context": list(),
                "plugins": list(),

                # Data internal to the GUI itself
                "is_running": False,
                "is_closing": False,
                "close_requested": False,

                # Transient state used during publishing
                # This is used to track whether or not to continue
                # processing when, for example, validation has failed.
                "processing": {
                    "nextOrder": None,
                    "ordersWithError": set()
                }
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

        # NOTE: Listeners to this signal are run in the main thread
        self.about_to_process.connect(self.on_about_to_process,
                                      QtCore.Qt.DirectConnection)

        left_view.toggled.connect(self.on_delegate_toggled)
        right_view.toggled.connect(self.on_delegate_toggled)
        reset.clicked.connect(self.on_reset_clicked)
        play.clicked.connect(self.on_play_clicked)
        stop.clicked.connect(self.on_stop_clicked)
        right_view.customContextMenuRequested.connect(
            self.on_plugin_action_menu_requested)

    def on_play_clicked(self):
        self.prepare_publish()

    def on_reset_clicked(self):
        self.prepare_reset()

    def on_stop_clicked(self):
        self.info("Stopping..")
        self.data["state"]["is_running"] = False

    def on_delegate_toggled(self, index, state=None):
        """An item is requesting to be toggled"""
        if not index.data(model.IsIdle):
            return self.info("Cannot toggle")

        if not index.data(model.IsOptional):
            return self.info("This item is mandatory")

        if state is None:
            state = not index.data(model.IsChecked)

        index.model().setData(index, state, model.IsChecked)

    def on_about_to_process(self, plugin, instance):
        """Reflect currently running pair in GUI"""

        if instance is not None:
            instance_model = self.data["models"]["instances"]
            index = instance_model.items.index(instance)
            index = instance_model.createIndex(index, 0)
            instance_model.setData(index, True, model.IsProcessing)
            instance_model.setData(index, False, model.IsIdle)

        plugin_model = self.data["models"]["plugins"]
        index = plugin_model.items.index(plugin)
        index = plugin_model.createIndex(index, 0)
        plugin_model.setData(index, True, model.IsProcessing)
        plugin_model.setData(index, False, model.IsIdle)

        self.info("Processing %s" % (index.data(model.Label)))

    def on_plugin_action_menu_requested(self, pos):
        """The user right-clicked on a plug-in
         __________
        |          |
        | Action 1 |
        | Action 2 |
        | Action 3 |
        |          |
        |__________|

        """

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

    def _iterator(self, plugins, context):
        """Yield next plug-in and instance to process.

        Arguments:
            plugins (list): Plug-ins to process
            context (pyblish.api.Context): Context to process
            state (dict): Shared state across entire iteration

        """

        state = self.data["state"]["processing"]
        test = pyblish.logic.registered_test()

        for plug, instance in pyblish.logic.Iterator(plugins, context):
            if not plug.active:
                continue

            if instance is not None and instance.data.get("publish") is False:
                continue

            state["nextOrder"] = plug.order

            if not self.data["state"]["is_running"]:
                raise StopIteration("Stopped")

            if test(**state):
                raise StopIteration("Stopped due to %s" % test(**state))

            yield plug, instance

    def _process(self, plugin, instance):
        """Produce `result` from `plugin` and `instance`

        :func:`_process` shares state with :func:`_iterator` such that
        an instance/plugin pair can be fetched and processed in isolation.

        """

        context = self.data["state"]["context"]

        state = self.data["state"]["processing"]
        state["nextOrder"] = plugin.order

        try:
            result = pyblish.plugin.process(plugin, context, instance)

        except Exception as e:
            raise Exception("Unknown error: %s" % e)

        else:
            # Make note of the order at which the
            # potential error error occured.
            has_error = result["error"] is not None
            if has_error:
                state["ordersWithError"].add(plugin.order)

        return result

    def prepare_reset(self):
        self.info("About to reset..")

        self.data["state"]["context"] = list()
        self.data["state"]["plugins"] = list()

        for m in self.data["models"].values():
            m.reset()

        for b in self.data["buttons"].values():
            b.hide()

        defer(500, self.reset)

    def reset(self):
        """Discover plug-ins and run collection"""
        self.info("Resetting..")

        self.data["state"]["is_running"] = True

        models = self.data["models"]

        plugins = pyblish.api.discover()
        context = pyblish.api.Context()

        # Store internally
        self.data["state"]["context"] = context
        self.data["state"]["plugins"] = plugins

        models = self.data["models"]

        for Plugin in plugins:
            models["plugins"].append(Plugin)

        collectors = list(
            p for p in plugins
            if pyblish.lib.inrange(
                p.order,
                base=pyblish.api.CollectorOrder)
        )

        def on_next():
            try:
                plugin, instance = iterator.next()
                self.about_to_process.emit(plugin, instance)

                defer(100, lambda: on_process(plugin, instance))

            except StopIteration:
                defer(100, lambda: on_finished(context))

            except Exception as e:
                # This should never happen; i.e. bug
                stack = traceback.format_exc(e)
                defer(500, lambda: self.finish_reset(error=stack))

        def on_process(plugin, instance):
            try:
                result = self._process(plugin, instance)

            except Exception as e:
                return defer(500, lambda: self.finish_reset(error=str(e)))

            else:
                models["plugins"].update_with_result(result)
                models["instances"].update_with_result(result)

                defer(10, on_next)

        def on_finished(context):
            for instance in context:
                models["instances"].append(instance)

            defer(500, self.finish_reset)

        iterator = self._iterator(collectors, context)
        defer(10, on_next)

    def finish_reset(self, error=None):
        if error is not None:
            self.info("An error occurred.\n\n%s" % error)

        self.info("Finishing up reset..")

        buttons = self.data["buttons"]
        buttons["play"].show()
        buttons["reset"].show()
        buttons["stop"].hide()

        self.data["state"]["is_running"] = False
        self.finished.emit()
        self.info("Reset finished.")

    def prepare_publish(self):
        self.info("Preparing publish..")

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        defer(5, self.publish)

    def publish(self):
        self.info("Publishing..")

        self.data["state"]["is_running"] = True

        models = self.data["models"]

        plugins = self.data["state"]["plugins"]
        context = self.data["state"]["context"]

        assert plugins is not None, "Must reset first"
        assert context is not None, "Must reset first"

        plugins = list(
            p for p in plugins
            if not pyblish.lib.inrange(
                p.order,
                base=pyblish.api.CollectorOrder)
        )

        def on_next():
            try:
                plugin, instance = iterator.next()
                self.about_to_process.emit(plugin, instance)

                defer(100, lambda: on_process(plugin, instance))

            except StopIteration:
                defer(100, lambda: on_finished(context))

            except Exception as e:
                # This should never happen; i.e. bug
                stack = traceback.format_exc(e)
                defer(500, lambda: self.finish_publish(error=stack))

        def on_process(plugin, instance):
            try:
                result = self._process(plugin, instance)

            except Exception as e:
                return defer(500, lambda: self.finish_publish(error=str(e)))

            else:
                models["plugins"].update_with_result(result)
                models["instances"].update_with_result(result)

                defer(10, on_next)

        def on_finished(context):
            defer(500, self.finish_publish)

        iterator = self._iterator(plugins, context)
        defer(10, on_next)

    def finish_publish(self, error=None):
        if error is not None:
            self.info("An error occurred.\n\n%s" % error)

        self.data["state"]["is_running"] = False

        plugin_model = self.data["models"]["plugins"]
        for index in plugin_model:
            plugin_model.setData(index, model.IsIdle, False)

        buttons = self.data["buttons"]
        buttons["reset"].show()
        buttons["stop"].hide()

        self.finished.emit()
        self.info("Finished")

    def prepare_action(self, plugin, action):
        self.info("Preparing action..")

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        self.data["state"]["is_running"] = True

        defer(100, lambda: self.run_action(plugin, action))
        self.info("Action prepared.")

    def run_action(self, plugin, action):
        models = self.data["models"]
        context = self.data["state"]["context"]

        def on_next():
            result = pyblish.plugin.process(plugin, context, None, action.id)
            models["plugins"].update_with_result(result)
            models["instances"].update_with_result(result)
            defer(500, self.finish_action)

        defer(100, on_next)
        self.info("Action running..")

    def finish_action(self, error=None):
        if error is not None:
            self.info("An error occurred.\n\n%s" % error)

        self.data["state"]["is_running"] = False

        buttons = self.data["buttons"]
        buttons["reset"].show()
        buttons["stop"].hide()
        self.info("Finished")

    def closeEvent(self, event):
        """Perform post-flight checks before closing

        Make sure processing of any kind is wrapped up before closing

        """

        if self.data["state"]["is_closing"]:
            self.info("Good bye")
            return super(Window, self).closeEvent(event)

        self.info("Closing..")

        # Display placeholder
        # TODO(marcus): Make something nice here
        body = self.findChild(QtWidgets.QWidget, "Body")
        body.hide()

        placeholder = self.findChild(QtWidgets.QWidget, "ClosingPlaceholder")
        placeholder.show()

        if self.data["state"]["is_running"]:
            self.info("..as soon as processing is finished..")
            self.data["state"]["is_running"] = False
            self.finished.connect(self.close)
            return event.ignore()

        self.data["state"]["is_closing"] = True

        # Explicitly clear potentially referenced data
        self.info("Cleaning up..")
        for instance in self.data["state"].get("context", []):
            del(instance)

        for plugin in self.data["state"].get("plugins", []):
            del(plugin)

        defer(200, self.close)
        return event.ignore()

    def info(self, message):
        """Print user-facing information

        At the moment, this simply prints. This is where you would implement
        a QLabel of sorts and display the information there.

        """

        info = self.findChild(QtWidgets.QLabel, "Info")
        info.setText(message)

        fade_effect = QtGui.QGraphicsOpacityEffect(info)
        info.setGraphicsEffect(fade_effect)

        timeline = QtCore.QSequentialAnimationGroup()

        on = QtCore.QPropertyAnimation(fade_effect, "opacity")
        on.setDuration(0)
        on.setStartValue(0)
        on.setEndValue(1)

        off = QtCore.QPropertyAnimation(fade_effect, "opacity")
        off.setDuration(0)
        off.setStartValue(1)
        off.setEndValue(0)

        fade = QtCore.QPropertyAnimation(fade_effect, "opacity")
        fade.setDuration(500)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)

        timeline.addAnimation(on)
        timeline.addPause(50)
        timeline.addAnimation(off)
        timeline.addPause(50)
        timeline.addAnimation(on)
        timeline.addPause(2000)
        timeline.addAnimation(fade)

        timeline.start(timeline.DeleteWhenStopped)

        # Store reference to prevent garbage collection
        self.__message_animation = timeline


def defer(delay, func):
    """Append artificial delay to `func`

    This aids in keeping the GUI feel responsive, but complicates logic
    when producing tests. To combat this, the environment variable ensures
    that every operation is synchonous.

    Arguments:
        delay (float): Delay multiplier; default 1, 0 means no delay
        func (callable): Any callable

    """

    delay *= float(os.getenv("PYBLISH_DELAY", 1))
    if delay > 0:
        return QtCore.QTimer.singleShot(delay, func)
    else:
        return func()
