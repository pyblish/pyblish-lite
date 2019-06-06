"""The Controller in a Model/View/Controller-based application
The graphical components of Pyblish Lite use this object to perform
publishing. It communicates via the Qt Signals/Slots mechanism
and has no direct connection to any graphics. This is important,
because this is how unittests are able to run without requiring
an active window manager; such as via Travis-CI.
"""
import sys

from .vendor.Qt import QtCore

import pyblish.api
import pyblish.util
import pyblish.logic

from . import util


class Controller(QtCore.QObject):

    # Emitted when the GUI is about to start processing;
    # e.g. resetting, validating or publishing.
    about_to_process = QtCore.Signal(object, object)

    # Emitted for each process
    was_processed = QtCore.Signal(dict)

    was_discovered = QtCore.Signal(bool)
    was_reset = QtCore.Signal()
    was_validated = QtCore.Signal()
    was_published = QtCore.Signal()
    was_acted = QtCore.Signal(dict)

    # Emitted when processing has finished
    was_finished = QtCore.Signal()

    PART_COLLECT = 'collect'
    PART_VALIDATE = 'validate'
    PART_EXTRACT = 'extract'
    PART_CONFORM = 'conform'

    def __init__(self, parent=None):
        super(Controller, self).__init__(parent)

        self.context = list()
        self.plugins = {}

        # Data internal to the GUI itself
        self.is_running = False

        # Transient state used during publishing.
        self.pair_generator = None        # Active producer of pairs
        self.current_pair = (None, None)  # Active pair
        self.current_error = None

        # This is used to track whether or not to continue
        # processing when, for example, validation has failed.
        self.processing = {
            "nextOrder": None,
            "ordersWithError": set()
        }

    def reset(self):
        """Discover plug-ins and run collection"""
        self.validated = False
        self.extracted = False
        self.context = pyblish.api.Context()

        self.last_plugins = self.plugins
        self.all_plugins = pyblish.api.discover()
        # Load collectors
        self.load_plugins(True)
        self.current_error = None
        # Process collectors load rest of plugins with collected instances
        self.collect()

        self.was_discovered.emit()

        for group, plugins_last in self.last_plugins.items():
            for plugin_last in plugins_last:
                if not plugin_last.optional:
                    continue
                for plugin_current in self.plugins.get(group, []):
                    if plugin_current.label == plugin_last.label:
                        if not plugin_current.optional:
                            break
                        setattr(plugin_current, 'active', plugin_last.active)
                        break
        self.last_plugins = list()

        self.pair_generator = None
        self.current_pair = (None, None)
        self.current_error = None

        self.processing = {
            "nextOrder": None,
            "ordersWithError": set()
        }

    def load_plugins(self, load_collector=False):
        self.test = pyblish.logic.registered_test()
        self.state = {
            "nextOrder": None,
            "ordersWithError": set()
        }

        targets = pyblish.logic.registered_targets() or ["default"]

        collectors = []
        validators = []
        extractors = []
        conforms = []
        plugins = pyblish.logic.plugins_by_targets(
            self.all_plugins, targets
        )

        for plugin in plugins:
            if load_collector:
                if plugin.order < (pyblish.api.CollectorOrder + 0.5):
                    collectors.append(plugin)
            else:
                if plugin.order < (pyblish.api.CollectorOrder + 0.5):
                    continue
                elif plugin.order < (pyblish.api.ValidatorOrder + 0.5):
                    validators.append(plugin)
                elif plugin.order < (pyblish.api.ExtractorOrder + 0.5):
                    extractors.append(plugin)
                else:
                    conforms.append(plugin)

        if not load_collector:
            collectors = self.plugins[self.PART_COLLECT]

        self.plugins = {
            self.PART_COLLECT: collectors,
            self.PART_VALIDATE: validators,
            self.PART_EXTRACT: extractors,
            self.PART_CONFORM: conforms
        }

        self.was_discovered.emit(load_collector)

    def on_validated(self):
        pyblish.api.emit("validated", context=self.context)
        self.was_validated.emit()

    def on_published(self):
        pyblish.api.emit("published", context=self.context)
        self.was_published.emit()

    def act(self, plugin, action):
        context = self.context

        def on_next():
            result = pyblish.plugin.process(plugin, context, None, action.id)
            self.was_acted.emit(result)

        util.defer(100, on_next)

    def emit_(self, signal, kwargs):
        pyblish.api.emit(signal, **kwargs)

    def _process(self, plugin, instance=None):
        """Produce `result` from `plugin` and `instance`
        :func:`process` shares state with :func:`_iterator` such that
        an instance/plugin pair can be fetched and processed in isolation.
        Arguments:
            plugin (pyblish.api.Plugin): Produce result using plug-in
            instance (optional, pyblish.api.Instance): Process this instance,
                if no instance is provided, context is processed.
        """

        self.processing["nextOrder"] = plugin.order

        try:
            result = pyblish.plugin.process(plugin, self.context, instance)

        except Exception as e:
            raise Exception("Unknown error({}): {}".format(
                plugin.__name__, str(e)
            ))

        else:
            # Make note of the order at which the
            # potential error error occured.
            has_error = result["error"] is not None
            if has_error:
                self.processing["ordersWithError"].add(plugin.order)

        return result

    def _plugin_collect(self, plugins, collect):
        output = []
        for plugin in plugins:
            if not plugin.active:
                pyblish.logic.log.debug("%s was inactive, skipping.." % plugin)
                continue

            self.state["nextOrder"] = plugin.order

            message = self.test(**self.state)
            if message:
                raise pyblish.logic.StopIteration("Stopped due to %s" % message)

            instances = pyblish.logic.instances_by_plugin(self.context, plugin)
            if collect:
                output.append([plugin, None])
            elif plugin.__instanceEnabled__:
                for instance in instances:
                    if instance.data.get("publish") is False:
                        pyblish.logic.log.debug("%s was inactive, skipping.." % instance)
                        continue

                    output.append([plugin, instance])

            else:
                output.append([plugin, None])
        return output

    def iterate_and_process(self, plugins, is_collect=False):
        """ Iterating inserted plugins with current context.
        Collectors do not contain instances, they are None when collecting!
        This process don't stop on one
        """
        for pair in self._plugin_collect(plugins, is_collect):
            plug, instance = pair
            if not plug.active:
                continue
            try:
                self.about_to_process.emit(plug, instance)
                if not is_collect:
                    if not instance.data.get("publish"):
                        continue

                self.processing["nextOrder"] = plug.order

                if self.test(**self.processing):
                    raise StopIteration(
                        "Stopped due to %s" % test(**self.processing)
                    )
                result = self._process(plug, instance)

                if result["error"] is not None:
                    self.current_error = result["error"]

                self.was_processed.emit(result)
            except Exception:
                exc_type, exc_msg, exc_tb = sys.exc_info()
                util.u_print(u"An unexpected error occurred:\n %s" % exc_msg)

    def collect(self):
        """ Iterate and process Collect plugins
        - load_plugins method is launched again when finished
        """
        self.iterate_and_process(self.plugins[self.PART_COLLECT], True)

        self.load_plugins()
        self.was_reset.emit()
        self.was_finished.emit()

    def validate(self):
        """ Iterate and process Validate plugins
        - self.validated is set to True when done so we know was processed
        """
        self.iterate_and_process(self.plugins[self.PART_VALIDATE])
        self.validated = True

        self.on_validated()
        self.was_finished.emit()

    def extract(self):
        """ Iterate and process Extract plugins
        """
        if not self.validated:
            self.validate()
        if self.current_error:
            return

        self.iterate_and_process(self.plugins[self.PART_EXTRACT])
        self.extracted = True

    def publish(self):
        """ Iterate and process Conform(Integrate) plugins
        - won't start if any extractor fails
        """
        if not self.extracted:
            self.extract()
        if self.current_error:
            return

        self.iterate_and_process(self.plugins[self.PART_CONFORM])

        self.on_published()
        self.was_finished.emit()

    def cleanup(self):
        """Forcefully delete objects from memory
        In an ideal world, this shouldn't be necessary. Garbage
        collection guarantees that anything without reference
        is automatically removed.
        However, because this application is designed to be run
        multiple times from the same interpreter process, extra
        case must be taken to ensure there are no memory leaks.
        Explicitly deleting objects shines a light on where objects
        may still be referenced in the form of an error. No errors
        means this was uneccesary, but that's ok.
        """

        for instance in self.context:
            del(instance)

        for plugin in self.plugins:
            del(plugin)
