import os
import traceback

from Qt import QtCore, QtWidgets, QtGui

import pyblish.api
import pyblish.util
import pyblish.logic

from . import model, view, util, delegate


class Window(QtWidgets.QDialog):
    """Main Window

    STATES:
        These are all possible states and their transitions.

          reset
            '
            '
            '
         ___v__
        |      |       reset
        | Idle |--------------------.
        |      |<-------------------'
        |      |
        |      |                   _____________
        |      |     validate     |             |    reset     # TODO
        |      |----------------->| In-progress |-----------.
        |      |                  |_____________|           '
        |      |<-------------------------------------------'
        |      |
        |      |                   _________                 _____________
        |      |      publish     |         |    publish    |             |
        |      |----------------->| Comment |-------------->| In-progress |---.
        |      |                  |_________|               |_____________|   '
        |      |<-------------------------------------------------------------'
        |______|

    TODO:
        There are notes spread throughout this project with the syntax:

        - TODO(username)

        The `username` is a quick and dirty indicator of who made the note
        and is by no means exclusive to that person in terms of seeing it
        done. Feel free to do, or make your own TODO's as you code. Just
        make sure the description is sufficient for anyone reading it for
        the first time to understand how to actually to it!

    PREPARE:
        Major functions have a corresponding "prepare_" function.
        This is where the GUI is setup before actually starting to
        process. When testing, these are *not* necessary.

    """

    # Emitted when the GUI is about to start processing;
    # e.g. resetting, validating or publishing.
    about_to_process = QtCore.Signal(object, object)

    # Emitted when processing has finished
    finished = QtCore.Signal()

    current_pair_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        icon = QtGui.QIcon(util.get_asset("img", "logo-extrasmall.png"))
        self.setWindowTitle("Pyblish")
        self.setWindowIcon(icon)

        """General layout
         __________________       _____________________
        |                  |     |       |       |     |
        |      Header      | --> | Tab   | Tab   | Tab |
        |__________________|     |_______|_______|_____|
        |                  |      _____________________
        |                  |     |                     |
        |                  |     |                     |
        |       Body       |     |                     |
        |                  | --> |        Page         |
        |                  |     |                     |
        |                  |     |                     |
        |__________________|     |_____________________|
        |                  |
        |      Footer      |
        |__________________|

        """

        header = QtWidgets.QWidget()

        artist_tab = QtWidgets.QRadioButton()
        overview_tab = QtWidgets.QRadioButton()
        terminal_tab = QtWidgets.QRadioButton()
        spacer = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout(header)
        layout.addWidget(artist_tab, 0)
        layout.addWidget(overview_tab, 0)
        layout.addWidget(terminal_tab, 0)
        layout.addWidget(spacer, 1)  # Compress items to the left
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        """Artist Page
         __________________
        |                  |
        | | ------------   |
        | | -----          |
        |                  |
        | | --------       |
        | | -------        |
        |                  |
        |__________________|

        """

        artist_page = QtWidgets.QWidget()

        artist_view = view.Item()

        artist_delegate = delegate.Artist()
        artist_view.setItemDelegate(artist_delegate)

        layout = QtWidgets.QVBoxLayout(artist_page)
        layout.addWidget(artist_view)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        """Overview Page
         ___________________
        |                  |
        | o ----- o----    |
        | o ----  o---     |
        | o ----  o----    |
        | o ----  o------  |
        |                  |
        |__________________|

        """

        overview_page = QtWidgets.QWidget()

        left_view = view.Item()
        right_view = view.Item()

        item_delegate = delegate.Item()
        left_view.setItemDelegate(item_delegate)
        right_view.setItemDelegate(item_delegate)

        layout = QtWidgets.QHBoxLayout(overview_page)
        layout.addWidget(left_view, 1)
        layout.addWidget(right_view, 1)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        """Terminal

         __________________
        |                  |
        |  \               |
        |   \              |
        |   /              |
        |  /  ______       |
        |                  |
        |__________________|

        """

        terminal_view = view.LogView()

        terminal_delegate = delegate.Terminal()
        terminal_view.setItemDelegate(terminal_delegate)

        terminal_page = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(terminal_page)
        layout.addWidget(terminal_view)
        layout.setContentsMargins(5, 5, 5, 5)

        # Add some room between window borders and contents
        body = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(body)
        layout.setContentsMargins(5, 5, 5, 0)
        layout.addWidget(artist_page)
        layout.addWidget(overview_page)
        layout.addWidget(terminal_page)

        """Footer
         ______________________
        |             ___  ___ |
        |            | o || > ||
        |            |___||___||
        |______________________|

        """

        footer = QtWidgets.QWidget()
        info = QtWidgets.QLabel()
        spacer = QtWidgets.QWidget()
        reset = QtWidgets.QPushButton(u"\uf021")  # fa-refresh
        validate = QtWidgets.QPushButton(u"\uf0c3")   # fa-flask
        play = QtWidgets.QPushButton(u"\uf04b")   # fa-play
        stop = QtWidgets.QPushButton(u"\uf04d")   # fa-stop

        layout = QtWidgets.QHBoxLayout(footer)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(info, 0)
        layout.addWidget(spacer, 1)
        layout.addWidget(reset, 0)
        layout.addWidget(validate, 0)
        layout.addWidget(play, 0)
        layout.addWidget(stop, 0)

        # Placeholder for when GUI is closing
        # TODO(marcus): Fade to black and the the user about what's happening
        closing_placeholder = QtWidgets.QWidget(self)
        closing_placeholder.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                          QtWidgets.QSizePolicy.Expanding)
        closing_placeholder.hide()

        """Comment Box
         ____________________________
        |> My comment                |
        |                            |
        |____________________________|

        """

        comment_box = QtWidgets.QTextEdit(self)
        comment_box.verticalScrollBar().hide()
        comment_placeholder = QtWidgets.QLabel(
            "Enter optional comment..", comment_box)
        comment_placeholder.move(6, 6)
        comment_placeholder.hide()
        comment_box.hide()

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(header, 0)
        layout.addWidget(body, 3)
        layout.addWidget(closing_placeholder, 1)
        layout.addWidget(footer, 0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        instance_model = model.Instance()
        plugin_model = model.Plugin()
        terminal_model = model.Terminal()

        artist_view.setModel(instance_model)
        left_view.setModel(instance_model)
        right_view.setModel(plugin_model)
        terminal_view.setModel(terminal_model)

        """Animation
           ___
          /   \
         |     |            ___
          \___/            /   \
                   ___    |     |
                  /   \    \___/
                 |     |
                  \___/

        """

        # Display info
        info_effect = QtWidgets.QGraphicsOpacityEffect(info)
        info.setGraphicsEffect(info_effect)

        timeline = QtCore.QSequentialAnimationGroup()

        on = QtCore.QPropertyAnimation(info_effect, "opacity")
        on.setDuration(0)
        on.setStartValue(0)
        on.setEndValue(1)

        off = QtCore.QPropertyAnimation(info_effect, "opacity")
        off.setDuration(0)
        off.setStartValue(1)
        off.setEndValue(0)

        fade = QtCore.QPropertyAnimation(info_effect, "opacity")
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

        info_animation = timeline

        # Show commentbox
        comment_animation = QtCore.QPropertyAnimation(comment_box, "geometry")
        comment_animation.setDuration(200)
        comment_animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        # CSS property
        # Highlight is enabled when a comment is requested, to
        # indicate to the user that the button is awaiting further input.
        play.setProperty("highlight", False)

        """Setup

        Widgets are referred to in CSS via their object-name. We
        use the same mechanism internally to refer to objects; so rather
        than storing widgets as self.my_widget, it is referred to as:

        >>> my_widget = self.findChild(QtWidgets.QWidget, "MyWidget")

        This way there is only ever a single method of referring to any widget.

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
            "Footer": footer,
            "Info": info,

            # Pages
            "Artist": artist_page,
            "Overview": overview_page,
            "Terminal": terminal_page,

            # Tabs
            "ArtistTab": artist_tab,
            "OverviewTab": overview_tab,
            "TerminalTab": terminal_tab,

            # Buttons
            "Play": play,
            "validate": validate,
            "Reset": reset,
            "Stop": stop,

            # Misc
            "CommentBox": comment_box,
            "CommentPlaceholder": comment_placeholder,
            "ClosingPlaceholder": closing_placeholder,
        }

        for name, widget in names.items():
            widget.setObjectName(name)

        # Enable CSS on plain QWidget objects
        for widget in (header,
                       body,
                       artist_page,
                       comment_box,
                       overview_page,
                       terminal_page,
                       footer,
                       play,
                       validate,
                       stop,
                       reset,
                       closing_placeholder):
            widget.setAttribute(QtCore.Qt.WA_StyledBackground)

        self.data = {
            "views": {
                "artist": artist_view,
                "left": left_view,
                "right": right_view,
                "terminal": terminal_view,
            },
            "models": {
                "instances": instance_model,
                "plugins": plugin_model,
                "terminal": terminal_model,
            },
            "tabs": {
                "artist": artist_tab,
                "overview": overview_tab,
                "terminal": terminal_tab,
            },
            "pages": {
                "artist": artist_page,
                "overview": overview_page,
                "terminal": terminal_page,
            },
            "buttons": {
                "play": play,
                "validate": validate,
                "stop": stop,
                "reset": reset
            },
            "animation": {
                "display_info": info_animation,
                "display_commentbox": comment_animation,
            },

            # This is the global application state. It is a shared
            # data structure amongst the various methods of this
            # class.
            #
            # It should *not* be accessed/modified asynchronously.
            #
            "state": {
                # These are internal caches of the data
                # visualised by the model. The model then
                # modified these objects as-is, such as their
                # "active" attribute or "artist" data.
                "context": list(),
                "plugins": list(),

                # Data internal to the GUI itself
                "is_running": False,
                "is_closing": False,
                "close_requested": False,
                "comment_offered": False,

                # Transient state used during publishing.
                "pair_generator": None,        # Active producer of pairs
                "current_pair": (None, None),  # Active pair
                "current_error": None,

                # This is used to track whether or not to continue
                # processing when, for example, validation has failed.
                "processing": {
                    "nextOrder": None,
                    "ordersWithError": set()
                },
            },
            "temp": {}  # Stores variables to prevent garbage collection
        }

        # Defaults
        self.on_tab_changed("artist")
        artist_tab.setChecked(True)

        """Signals
         ________     ________
        |________|-->|________|
                         |
                         |
                      ___v____
                     |________|

        """

        # NOTE: Listeners to this signal are run in the main thread
        artist_tab.released.connect(
            lambda: self.on_tab_changed("artist"))
        overview_tab.released.connect(
            lambda: self.on_tab_changed("overview"))
        terminal_tab.released.connect(
            lambda: self.on_tab_changed("terminal"))

        self.about_to_process.connect(self.on_about_to_process,
                                      QtCore.Qt.DirectConnection)
        self.finished.connect(self.on_finished)

        artist_view.toggled.connect(self.on_delegate_toggled)
        left_view.toggled.connect(self.on_delegate_toggled)
        right_view.toggled.connect(self.on_delegate_toggled)
        reset.clicked.connect(self.on_reset_clicked)
        validate.clicked.connect(self.on_validate_clicked)
        play.clicked.connect(self.on_play_clicked)
        stop.clicked.connect(self.on_stop_clicked)
        comment_box.textChanged.connect(self.on_comment_entered)
        right_view.customContextMenuRequested.connect(
            self.on_plugin_action_menu_requested)

    def on_tab_changed(self, target):
        for tab in self.data["pages"].values():
            tab.hide()

        tab = self.data["pages"][target]
        radio = self.data["tabs"][target]

        tab.show()
        radio.setChecked(True)

    def on_validate_clicked(self):
        self.prepare_validate()

    def on_play_clicked(self):
        if not self.data["state"]["comment_offered"]:
            return self.offer_commentbox()

        self.prepare_publish()

    def on_reset_clicked(self):
        self.prepare_reset()

    def on_stop_clicked(self):
        self.info("Stopping..")
        self.data["state"]["is_running"] = False

    def on_comment_entered(self):
        """The user has typed a comment"""
        text_edit = self.findChild(QtWidgets.QTextEdit, "CommentBox")
        comment = text_edit.toPlainText()
        context = self.data["state"]["context"]
        context.data['comment'] = comment

        placeholder = self.findChild(QtWidgets.QLabel, "CommentPlaceholder")
        placeholder.setVisible(not comment)

    def on_delegate_toggled(self, index, state=None):
        """An item is requesting to be toggled"""
        if not index.data(model.IsIdle):
            return self.info("Cannot toggle")

        if not index.data(model.IsOptional):
            return self.info("This item is mandatory")

        if state is None:
            state = not index.data(model.IsChecked)

        index.model().setData(index, state, model.IsChecked)

        # Withdraw option to publish if no instances are toggled
        play = self.findChild(QtWidgets.QWidget, "Play")
        play.setEnabled(any(index.data(model.IsChecked)
                            for index in self.data["models"]["instances"]))

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
                lambda p=plugin, a=action: self.prepare_action(p, a)
            )
            menu.addAction(qaction)

        menu.popup(self.data["views"]["right"].viewport().mapToGlobal(pos))

    def offer_commentbox(self):
        """Provide an option to enter a comment"""

        comment_box = self.findChild(QtWidgets.QWidget, "CommentBox")
        play = self.findChild(QtWidgets.QWidget, "Play")
        body = self.findChild(QtWidgets.QWidget, "Body")

        # Update geometry for comment
        ratio = 1.0 / 4  # Cover quarter of body
        height = body.geometry().height() - body.geometry().height() * ratio
        end = body.geometry().adjusted(0, height, 0, 0)
        start = end.adjusted(0, end.height() - 40, 0, 0)

        animation = self.data["animation"]["display_commentbox"]
        animation.setStartValue(start)
        animation.setEndValue(end)

        animation.stop()
        animation.start()

        play.setProperty("highlight", True)
        play.style().unpolish(play)
        play.style().polish(play)

        comment_box.raise_()
        comment_box.show()

        self.data["state"]["comment_offered"] = True
        self.info("Comment offered")

    def withdraw_comment(self):
        """Remove comment box"""

        comment_box = self.findChild(QtWidgets.QWidget, "CommentBox")
        comment_box.hide()

        play = self.findChild(QtWidgets.QWidget, "Play")
        play.setProperty("highlight", False)
        play.style().unpolish(play)
        play.style().polish(play)

        self.data["state"]["comment_offered"] = False

        self.info("Comment withdrawn")

    def load(self):
        """Initiate new generator and load first pair"""
        state = self.data["state"]

        state["pair_generator"] = self._iterator(state["plugins"],
                                                 state["context"])
        state["current_pair"] = next(state["pair_generator"], (None, None))
        state["current_error"] = None

    def run(self, until, on_finished):
        """Process current pair and store next pair for next process

        Arguments:
            until (pyblish.api.Order): Keep fetching next() until this order
            on_finished (callable): Mandatory handler finished state,
                takes no arguments.

        """

        state = self.data["state"]
        models = self.data["models"]

        def on_next():
            if state["current_pair"] == (None, None):
                return defer(100, on_finished)

            # The magic number 0.5 is the range between
            # the various CVEI processing stages;
            # e.g.
            #  - Collection is 0 +- 0.5 (-0.5 - 0.5)
            #  - Validation is 1 +- 0.5 (0.5  - 1.5)
            #
            # TODO(marcus): Make this less magical
            #
            if state["current_pair"][0].order > (until + 0.5):
                return defer(100, on_finished)

            self.about_to_process.emit(*state["current_pair"])

            defer(10, on_process)

        def on_process():
            try:
                result = self._process(*state["current_pair"])

                if result["error"] is not None:

                    # Log the error to the terminal
                    self.info(str(result["error"]))

                    self.data["state"]["current_error"] = result["error"]

                models["plugins"].update_with_result(result)
                models["instances"].update_with_result(result)
                models["terminal"].update_with_result(result)

            except Exception as e:
                stack = traceback.format_exc(e)
                return defer(500, lambda: on_unexpected_error(error=stack))

            # Now that processing has completed, and context potentially
            # modified with new instances, produce the next pair.
            #
            # IMPORTANT: This *must* be done *after* processing of
            # the current pair, otherwise data generated at that point
            # will *not* be included.
            try:
                state["current_pair"] = next(state["pair_generator"])

            except StopIteration:
                # All pairs were processed successfully!
                state["current_pair"] = (None, None)
                return defer(500, on_finished)

            except Exception as e:
                # This is a bug
                stack = traceback.format_exc(e)
                state["current_pair"] = (None, None)
                return defer(500, lambda: on_unexpected_error(error=stack))

            defer(10, on_next)

        def on_unexpected_error(error):
            self.warning("An unexpected error occurred; "
                         "see Terminal for more.")
            return defer(500, on_finished)

        defer(10, on_next)

    def _iterator(self, plugins, context):
        """Yield next plug-in and instance to process.

        Arguments:
            plugins (list): Plug-ins to process
            context (pyblish.api.Context): Context to process

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

    def _process(self, plugin, instance=None):
        """Produce `result` from `plugin` and `instance`

        :func:`_process` shares state with :func:`_iterator` such that
        an instance/plugin pair can be fetched and processed in isolation.

        Arguments:
            plugin (pyblish.api.Plugin): Produce result using plug-in
            instance (optional, pyblish.api.Instance): Process this instance,
                if no instance is provided, context is processed.

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
        """Prepare GUI for reset"""
        self.info("About to reset..")

        self.withdraw_comment()

        models = self.data["models"]

        models["instances"].store_checkstate()
        models["plugins"].store_checkstate()

        for m in models.values():
            m.reset()

        for b in self.data["buttons"].values():
            b.hide()

        defer(500, self._reset)

    def _reset(self):
        """Discover plug-ins and run collection"""
        self.info("Resetting..")

        self.data["state"].update({
            "context": pyblish.api.Context(),
            "plugins": pyblish.api.discover(),

            "is_running": True,

            "pair_generator": None,
            "current_pair": (None, None),
            "current_error": None,

            "processing": {
                "nextOrder": None,
                "ordersWithError": set()
            }
        })

        models = self.data["models"]

        for Plugin in self.data["state"]["plugins"]:
            models["plugins"].append(Plugin)

        def on_finished():
            self.data["state"]["is_running"] = False

            # For the intents and purposes of continue processing,
            # we don't care about errors that occur here.
            self.data["state"]["current_error"] = None

            for instance in self.data["state"]["context"]:
                models["instances"].append(instance)

            self.info("Finishing up reset..")

            buttons = self.data["buttons"]
            buttons["play"].show()
            buttons["validate"].show()
            buttons["reset"].show()
            buttons["stop"].hide()

            models["instances"].restore_checkstate()
            models["plugins"].restore_checkstate()

            defer(500, self.finished.emit)

        # Initialise comment box
        self.on_comment_entered()

        self.load()
        self.run(until=pyblish.api.CollectorOrder, on_finished=on_finished)

    def prepare_validate(self):
        self.info("Preparing validate..")

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        defer(5, self._validate)


    def _validate(self):
        self.info("Validate..")

        self.data["state"]["is_running"] = True

        def on_finished():
            plugin_model = self.data["models"]["plugins"]
            instance_model = self.data["models"]["instances"]

            for index in plugin_model:
                index.model().setData(index, False, model.IsIdle)

            for index in instance_model:
                index.model().setData(index, False, model.IsIdle)

            buttons = self.data["buttons"]
            buttons["reset"].show()
            buttons["play"].show()
            buttons["stop"].hide()

            defer(500, self.finished.emit)

        self.run(until=pyblish.api.ValidatorOrder, on_finished=on_finished)


    def prepare_publish(self):
        self.info("Preparing publish..")

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        self.withdraw_comment()
        defer(5, self._publish)

    def _publish(self):
        self.info("Publishing..")

        self.data["state"]["is_running"] = True

        def on_finished():
            plugin_model = self.data["models"]["plugins"]
            instance_model = self.data["models"]["instances"]

            for index in plugin_model:
                index.model().setData(index, False, model.IsIdle)

            for index in instance_model:
                index.model().setData(index, False, model.IsIdle)

            buttons = self.data["buttons"]
            buttons["reset"].show()
            buttons["stop"].hide()

            defer(500, self.finished.emit)

        self.run(until=pyblish.api.IntegratorOrder, on_finished=on_finished)

    def on_finished(self):
        """Finished signal handler"""
        self.data["state"]["is_running"] = False

        error = self.data["state"]["current_error"]
        if error is not None:
            self.info(str(error))
            self.info("Stopped due to error(s), see Terminal.")
        else:
            self.info("Finished successfully!")

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
            models["terminal"].update_with_result(result)
            defer(500, on_finished)

        def on_finished():
            buttons = self.data["buttons"]
            buttons["reset"].show()
            buttons["stop"].hide()

            self.finished.emit()

        defer(100, on_next)
        self.info("Action running..")

    def closeEvent(self, event):
        """Perform post-flight checks before closing

        Make sure processing of any kind is wrapped up before closing

        """

        # Make it snappy, but take care to clean it all up.
        # TODO(marcus): Enable GUI to return on problem, such
        # as asking whether or not the user really wants to quit
        # given there are things currently running.
        self.hide()

        if self.data["state"]["is_closing"]:

            # Explicitly clear potentially referenced data
            self.info("Cleaning up models..")
            for v in self.data["views"].values():
                v.model().deleteLater()
                v.setModel(None)

            self.info("Cleaning up instances..")
            for instance in self.data["state"].get("context", []):
                del(instance)

            self.info("Cleaning up plugins..")
            for plugin in self.data["state"].get("plugins", []):
                del(plugin)

            self.info("Cleaning up terminal..")
            for item in self.data["models"]["terminal"].items:
                del(item)

            self.info("All clean!")
            self.info("Good bye")
            return super(Window, self).closeEvent(event)

        self.info("Closing..")

        def on_problem():
            self.heads_up("Warning", "Had trouble closing down. "
                          "Please tell someone and try again.")

        if self.data["state"]["is_running"]:
            self.info("..as soon as processing is finished..")
            self.data["state"]["is_running"] = False
            self.finished.connect(self.close)
            defer(2000, on_problem)
            return event.ignore()

        self.data["state"]["is_closing"] = True

        defer(200, self.close)
        return event.ignore()

    def reject(self):
        """Handle ESC key"""

        if self.data["state"]["is_running"]:
            self.info("Stopping..")
            self.data["state"]["is_running"] = False

        if self.data["state"]["comment_offered"]:
            self.withdraw_comment()

    def info(self, message):
        """Print user-facing information

        Arguments:
            message (str): Text message for the user

        """

        info = self.findChild(QtWidgets.QLabel, "Info")
        info.setText(message)

        # Include message in terminal
        self.data["models"]["terminal"].append({
            "label": message,
            "type": "info"
        })

        animation = self.data["animation"]["display_info"]
        animation.stop()
        animation.start()

        # TODO(marcus): Should this be configurable? Do we want
        # the shell to fill up with these messages?
        print(message)

    def warning(self, message):
        """Block processing and print warning until user hits "Continue"

        Arguments:
            message (str): Message to display

        """

        # TODO(marcus): Implement this.
        self.info(message)

    def heads_up(self, title, message, command=None):
        """Provide a front-and-center message with optional command

        Arguments:
            title (str): Bold and short message
            message (str): Extended message
            command (optional, callable): Function is provided as a button

        """

        # TODO(marcus): Implement this.
        self.info(message)


def defer(delay, func):
    """Append artificial delay to `func`

    This aids in keeping the GUI responsive, but complicates logic
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
