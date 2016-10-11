"""Main Window

States:
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
    |      |                   _____________
    |      |      publish     |             |
    |      |----------------->| In-progress |---.
    |      |                  |_____________|   '
    |      |<-----------------------------------'
    |______|


Todo:
    There are notes spread throughout this project with the syntax:

    - TODO(username)

    The `username` is a quick and dirty indicator of who made the note
    and is by no means exclusive to that person in terms of seeing it
    done. Feel free to do, or make your own TODO's as you code. Just
    make sure the description is sufficient for anyone reading it for
    the first time to understand how to actually to it!

"""

from .vendor.Qt import QtCore, QtWidgets, QtGui

from . import model, view, util, delegate, settings
from .awesome import tags as awesome


class Window(QtWidgets.QDialog):
    def __init__(self, controller, parent=None):
        super(Window, self).__init__(parent)
        icon = QtGui.QIcon(util.get_asset("img", "logo-extrasmall.png"))
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowTitleHint |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint |
                            QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle(settings.WindowTitle)
        self.setWindowIcon(icon)

        self.controller = controller

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
        |                  |     |_____________________|
        |__________________|      _____________________
        |                  |     |           |         |
        |      Footer      |     | Status    | Buttons |
        |__________________|     |___________|_________|

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

        terminal_container = QtWidgets.QWidget()

        terminal_delegate = delegate.Terminal()
        terminal_view = view.LogView()
        terminal_view.setItemDelegate(terminal_delegate)

        layout = QtWidgets.QVBoxLayout(terminal_container)
        layout.addWidget(terminal_view)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        terminal_footer = QtWidgets.QWidget()

        search_box = QtWidgets.QLineEdit()
        instance_combo = QtWidgets.QComboBox()
        plugin_combo = QtWidgets.QComboBox()
        show_errors = QtWidgets.QCheckBox()
        show_records = QtWidgets.QCheckBox()
        show_debug = QtWidgets.QCheckBox()
        show_info = QtWidgets.QCheckBox()
        show_warning = QtWidgets.QCheckBox()
        show_error = QtWidgets.QCheckBox()
        show_critical = QtWidgets.QCheckBox()

        layout = QtWidgets.QHBoxLayout(terminal_footer)
        for w in (search_box,
                  instance_combo,
                  plugin_combo,
                  show_errors,
                  show_records,
                  show_debug,
                  show_info,
                  show_warning,
                  show_error,
                  show_critical):
            layout.addWidget(w)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        terminal_page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(terminal_page)
        layout.addWidget(terminal_container)
        # layout.addWidget(terminal_footer)  # TODO
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add some room between window borders and contents
        body = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(body)
        layout.setContentsMargins(5, 5, 5, 0)
        layout.addWidget(artist_page)
        layout.addWidget(overview_page)
        layout.addWidget(terminal_page)

        """Comment Box
         ____________________________
        |> My comment                |
        |                            |
        |____________________________|

        """

        comment_box = QtWidgets.QLineEdit()
        comment_placeholder = QtWidgets.QLabel("Comment..", comment_box)
        comment_placeholder.move(2, 2)
        comment_box.setEnabled(False)
        comment_box.hide()

        """Details View
         ____________________________
        |                            |
        | An Item              23 ms |
        | - family                   |
        |                            |
        |----------------------------|
        |                            |
        | Docstring                  |
        |____________________________|

        """

        details = view.Details(self)

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
        reset = QtWidgets.QPushButton(awesome["refresh"])
        validate = QtWidgets.QPushButton(awesome["flask"])
        play = QtWidgets.QPushButton(awesome["play"])
        stop = QtWidgets.QPushButton(awesome["stop"])

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

        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(header, 0)
        layout.addWidget(body, 3)
        layout.addWidget(closing_placeholder, 1)
        layout.addWidget(comment_box, 0)
        layout.addWidget(footer, 0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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

        on = QtCore.QPropertyAnimation(info_effect, b"opacity")
        on.setDuration(0)
        on.setStartValue(0)
        on.setEndValue(1)

        off = QtCore.QPropertyAnimation(info_effect, b"opacity")
        off.setDuration(0)
        off.setStartValue(1)
        off.setEndValue(0)

        fade = QtCore.QPropertyAnimation(info_effect, b"opacity")
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

        instance_model = model.Instance()
        plugin_model = model.Plugin()
        terminal_model = model.Terminal()

        artist_view.setModel(instance_model)
        left_view.setModel(instance_model)
        right_view.setModel(plugin_model)
        terminal_view.setModel(terminal_model)

        instance_combo.setModel(instance_model)
        plugin_combo.setModel(plugin_model)

        names = {
            # Main
            "Header": header,
            "Body": body,
            "Footer": footer,
            "Info": info,

            # Modals
            "Details": details,

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
            "Validate": validate,
            "Reset": reset,
            "Stop": stop,

            # Misc
            "CommentBox": comment_box,
            "CommentPlaceholder": comment_placeholder,
            "ClosingPlaceholder": closing_placeholder,
        }

        for name, w in names.items():
            w.setObjectName(name)

        # Enable CSS on plain QWidget objects
        for w in (header,
                  body,
                  artist_page,
                  comment_box,
                  overview_page,
                  terminal_page,
                  footer,
                  play,
                  validate,
                  stop,
                  details,
                  reset,
                  closing_placeholder):
            w.setAttribute(QtCore.Qt.WA_StyledBackground)

        self.data = {
            "views": {
                "artist": artist_view,
                "left": left_view,
                "right": right_view,
                "terminal": terminal_view,
            },
            "modals": {
                "details": details,
            },
            "models": {
                "instances": instance_model,
                "plugins": plugin_model,
                "terminal": terminal_model,
            },
            "terminal_toggles": {
                "record": show_records,
                "debug": show_debug,
                "info": show_info,
                "warning": show_warning,
                "error": show_error,
                "critical": show_critical
            },
            "tabs": {
                "artist": artist_tab,
                "overview": overview_tab,
                "terminal": terminal_tab,
                "current": "artist"
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
            },

            "state": {
                "is_closing": False,
            }
        }

        # Pressing Enter defaults to Play
        play.setFocus()

        """Signals
         ________     ________
        |________|-->|________|
                         |
                         |
                      ___v____
                     |________|

        """

        artist_tab.toggled.connect(
            lambda: self.on_tab_changed("artist"))
        overview_tab.toggled.connect(
            lambda: self.on_tab_changed("overview"))
        terminal_tab.toggled.connect(
            lambda: self.on_tab_changed("terminal"))

        controller.was_reset.connect(self.on_was_reset)
        controller.was_validated.connect(self.on_was_validated)
        controller.was_published.connect(self.on_was_published)
        controller.was_acted.connect(self.on_was_acted)
        controller.finished.connect(self.on_finished)

        # Discovery happens synchronously during reset, that's
        # why it's important that this connection is triggered
        # right away.
        controller.was_discovered.connect(self.on_was_discovered,
                                          QtCore.Qt.DirectConnection)

        # This is called synchronously on each process
        controller.was_processed.connect(self.on_was_processed,
                                         QtCore.Qt.DirectConnection)

        # NOTE: Listeners to this signal are run in the main thread
        controller.about_to_process.connect(self.on_about_to_process,
                                            QtCore.Qt.DirectConnection)

        artist_view.toggled.connect(self.on_item_toggled)
        left_view.toggled.connect(self.on_item_toggled)
        right_view.toggled.connect(self.on_item_toggled)

        artist_view.inspected.connect(self.on_item_inspected)
        left_view.inspected.connect(self.on_item_inspected)
        right_view.inspected.connect(self.on_item_inspected)
        terminal_view.inspected.connect(self.on_item_inspected)

        reset.clicked.connect(self.on_reset_clicked)
        validate.clicked.connect(self.on_validate_clicked)
        play.clicked.connect(self.on_play_clicked)
        stop.clicked.connect(self.on_stop_clicked)
        comment_box.textChanged.connect(self.on_comment_entered)
        comment_box.returnPressed.connect(self.on_play_clicked)
        right_view.customContextMenuRequested.connect(
            self.on_plugin_action_menu_requested)

        for box in (show_errors,
                    show_records,
                    show_debug,
                    show_info,
                    show_warning,
                    show_error,
                    show_critical):
            box.setChecked(True)

        self.data["tabs"][settings.InitialTab].setChecked(True)

    # -------------------------------------------------------------------------
    #
    # Event handlers
    #
    # -------------------------------------------------------------------------

    def on_item_expanded(self, index, state):
        if not index.data(model.IsExpandable):
            return

        if state is None:
            state = not index.data(model.Expanded)

        # Collapse others
        for i in index.model():
            index.model().setData(i, False, model.Expanded)

        index.model().setData(index, state, model.Expanded)

    def on_item_inspected(self, index):
        details = self.data["modals"]["details"]
        details.move(QtGui.QCursor.pos())

        if index.data(model.Type) == "record":

            # Compose available data
            data = list()
            for key, value in index.data(model.Data).items():
                if key.startswith("_"):
                    continue

                data.append("%s %s" % ((key + ":").ljust(12), value))

            text = "\n".join(data)

            details.show({
                "icon": awesome["circle"],
                "heading": index.data(model.Label).split("\n")[0],
                "subheading": "LogRecord (%s)" % index.data(model.LogLevel),
                "text": text,
                "timestamp": "",
            })

        elif index.data(model.Type) == "error":

            # Compose available data
            data = list()
            for key, value in index.data(model.Data).items():
                if key.startswith("_"):
                    continue

                data.append("%s %s" % ((key + ":").ljust(12), value))

            text = "\n".join(data)

            details.show({
                "icon": awesome["exclamation-triangle"],
                "heading": index.data(model.Label).split("\n")[0],
                "subheading": "Exception",
                "text": text,
                "timestamp": "",
            })

        elif index.data(model.Type) == "plugin":
            details.show({
                "icon": index.data(model.Icon) or awesome["filter"],
                "heading": index.data(model.Label),
                "subheading": ", ".join(index.data(model.Families)),
                "text": index.data(model.Docstring) or "",
                "timestamp": str(index.data(model.Duration) or 0) + " ms",
            })

        elif index.data(model.Type) == "instance":
            details.show({
                "icon": index.data(model.Icon) or awesome["file"],
                "heading": index.data(model.Label),
                "subheading": ", ".join(index.data(model.Families)),
                "text": "",
                "timestamp": str(index.data(model.Duration) or 0) + " ms",
            })

    def on_item_toggled(self, index, state=None):
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
        validate = self.findChild(QtWidgets.QWidget, "Validate")
        any_instances = any(index.data(model.IsChecked)
                            for index in self.data["models"]["instances"])
        play.setEnabled(any_instances)
        validate.setEnabled(any_instances)

        # Emit signals
        if index.data(model.Type) == "instance":
            util.defer(
                100, lambda: self.controller.emit_(
                    signal="instanceToggled",
                    kwargs={"new_value": state,
                            "old_value": not state,
                            "instance": index.data(model.Object)}))

        if index.data(model.Type) == "plugin":
            util.defer(
                100, lambda: self.controller.emit_(
                    signal="pluginToggled",
                    kwargs={"new_value": state,
                            "old_value": not state,
                            "plugin": index.data(model.Object)}))

    def on_tab_changed(self, target):
        for page in self.data["pages"].values():
            page.hide()

        page = self.data["pages"][target]

        comment_box = self.findChild(QtWidgets.QWidget, "CommentBox")

        if target == "terminal":
            comment_box.hide()
        else:
            comment_box.setVisible(comment_box.isEnabled())

        page.show()

        self.data["tabs"]["current"] = target

    def on_validate_clicked(self):
        comment_box = self.findChild(QtWidgets.QWidget, "CommentBox")
        comment_box.setEnabled(False)
        comment_box.hide()
        self.validate()

    def on_play_clicked(self):
        comment_box = self.findChild(QtWidgets.QWidget, "CommentBox")
        comment_box.setEnabled(False)
        comment_box.hide()
        self.publish()

    def on_reset_clicked(self):
        self.reset()

    def on_stop_clicked(self):
        self.info("Stopping..")
        self.controller.is_running = False

    def on_comment_entered(self):
        """The user has typed a comment"""
        text_edit = self.findChild(QtWidgets.QWidget, "CommentBox")
        comment = text_edit.text()

        # Store within context
        context = self.controller.context
        context.data["comment"] = comment

        placeholder = self.findChild(QtWidgets.QLabel, "CommentPlaceholder")
        placeholder.setVisible(not comment)

    def on_about_to_process(self, plugin, instance):
        """Reflect currently running pair in GUI"""

        if instance is not None:
            instance_model = self.data["models"]["instances"]
            index = instance_model.items.index(instance)
            index = instance_model.createIndex(index, 0)
            instance_model.setData(index, True, model.IsProcessing)

        plugin_model = self.data["models"]["plugins"]
        index = plugin_model.items.index(plugin)
        index = plugin_model.createIndex(index, 0)
        plugin_model.setData(index, True, model.IsProcessing)

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
        print("plugin is: %s" % plugin)

        for action in actions:
            qaction = QtWidgets.QAction(action.label or action.__name__, self)
            qaction.triggered.connect(
                lambda p=plugin, a=action: self.act(p, a)
            )
            menu.addAction(qaction)

        menu.popup(self.data["views"]["right"].viewport().mapToGlobal(pos))

    def on_was_discovered(self):
        models = self.data["models"]

        for Plugin in self.controller.plugins:
            models["plugins"].append(Plugin)

    def on_was_reset(self):
        models = self.data["models"]

        for instance in self.controller.context:
            models["instances"].append(instance)

        self.info("Finishing up reset..")

        buttons = self.data["buttons"]
        buttons["play"].show()
        buttons["validate"].show()
        buttons["reset"].show()
        buttons["stop"].hide()

        models["instances"].restore_checkstate()
        models["plugins"].restore_checkstate()

        # Append placeholder comment from Context
        # This allows users to inject a comment from elsewhere,
        # or to perhaps provide a placeholder comment/template
        # for artists to fill in.
        comment = self.controller.context.data.get("comment")

        comment_box = self.findChild(QtWidgets.QWidget, "CommentBox")
        comment_box.setText(comment or None)
        comment_box.setEnabled(comment is not None)

        # Refresh tab
        self.on_tab_changed(self.data["tabs"]["current"])

        self.controller.current_error = None
        util.defer(500, self.on_finished)

    def on_was_validated(self):
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

        util.defer(500, self.on_finished)

    def on_was_published(self):
        plugin_model = self.data["models"]["plugins"]
        instance_model = self.data["models"]["instances"]

        for index in plugin_model:
            index.model().setData(index, False, model.IsIdle)

        for index in instance_model:
            index.model().setData(index, False, model.IsIdle)

        buttons = self.data["buttons"]
        buttons["reset"].show()
        buttons["stop"].hide()

        comment_box = self.findChild(QtWidgets.QWidget, "CommentBox")
        comment_box.hide()

        util.defer(500, self.on_finished)

    def on_was_processed(self, result):
        models = self.data["models"]

        models["plugins"].update_with_result(result)
        models["instances"].update_with_result(result)
        models["terminal"].update_with_result(result)

    def on_was_acted(self, result):
        buttons = self.data["buttons"]
        buttons["reset"].show()
        buttons["stop"].hide()

        # Update action with result
        model_ = self.data["models"]["plugins"]

        index = model_.items.index(result["plugin"])
        index = model_.createIndex(index, 0)

        model_.setData(index, not result["success"], model.ActionFailed)
        model_.setData(index, False, model.IsProcessing)

        models = self.data["models"]
        models["terminal"].update_with_result(result)

        self.on_finished()

    def on_finished(self):
        """Finished signal handler"""
        self.controller.is_running = False

        error = self.controller.current_error
        if error is not None:
            self.info("Stopped due to error(s), see Terminal.")
        else:
            self.info("Finished successfully!")

    # -------------------------------------------------------------------------
    #
    # Functions
    #
    # -------------------------------------------------------------------------

    def reset(self):
        """Prepare GUI for reset"""
        self.info("About to reset..")

        models = self.data["models"]

        models["instances"].store_checkstate()
        models["plugins"].store_checkstate()

        for m in models.values():
            m.reset()

        for b in self.data["buttons"].values():
            b.hide()

        comment_box = self.findChild(QtWidgets.QWidget, "CommentBox")
        comment_box.hide()

        util.defer(500, self.controller.reset)

    def validate(self):
        self.info("Preparing validate..")

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        util.defer(5, self.controller.validate)

    def publish(self):
        self.info("Preparing publish..")

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        util.defer(5, self.controller.publish)

    def act(self, plugin, action):
        self.info("Preparing %s.." % action)

        for button in self.data["buttons"].values():
            button.hide()

        self.data["buttons"]["stop"].show()
        self.controller.is_running = True

        # Cause view to update, but it won't visually
        # happen until Qt is given time to idle..
        model_ = self.data["models"]["plugins"]

        index = model_.items.index(plugin)
        index = model_.createIndex(index, 0)

        for key, value in {model.ActionIdle: False,
                           model.ActionFailed: False,
                           model.IsProcessing: True}.items():
            model_.setData(index, value, key)

        # Give Qt time to draw
        util.defer(100, lambda: self.controller.act(plugin, action))

        self.info("Action prepared.")

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

            self.info("Cleaning up terminal..")
            for item in self.data["models"]["terminal"].items:
                del(item)

            self.info("Cleaning up controller..")
            self.controller.cleanup()

            self.info("All clean!")
            self.info("Good bye")
            return super(Window, self).closeEvent(event)

        self.info("Closing..")

        def on_problem():
            self.heads_up("Warning", "Had trouble closing down. "
                          "Please tell someone and try again.")
            self.show()

        if self.controller.is_running:
            self.info("..as soon as processing is finished..")
            self.controller.is_running = False
            self.finished.connect(self.close)
            util.defer(2000, on_problem)
            return event.ignore()

        self.data["state"]["is_closing"] = True

        util.defer(200, self.close)
        return event.ignore()

    def reject(self):
        """Handle ESC key"""

        if self.controller.is_running:
            self.info("Stopping..")
            self.controller.is_running = False

    # -------------------------------------------------------------------------
    #
    # Feedback
    #
    # -------------------------------------------------------------------------

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
