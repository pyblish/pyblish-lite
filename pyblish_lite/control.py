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

    was_discovered = QtCore.Signal()
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

        self.context = pyblish.api.Context()
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

    def prepare_for_reset(self):
        self.validated = False
        self.extracted = False
        self.publishing = False

        self.context = pyblish.api.Context()
        self.context.data["optional"] = False
        self.context.data["publish"] = True

        self.context.data["label"] = 'Context'
        self.context.data["name"] = 'Context'
        self.context.data["_type"] = 'context'

        self.context.data["icon"] = 'book'

        self.context.data["_has_succeeded"] = False
        self.context.data["_has_failed"] = False
        self.context.data["_is_idle"] = True

        self.context.data["__families__"] = ('__context__',)

    def reset(self):
        """
        Discover plug-ins and run collection
        - prepare_for_reset should be run before
            - was split because of `Context` in instance list
            - reset logic should be used only in window.py in `reset` method
        """
        # This is just backup
        if self.context:
            # - Context probably won't be shown in instance list
            self.prepare_for_reset()

        # Load collectors
        self.load_plugins()
        self.current_error = None
        # Process collectors load rest of plugins with collected instances
        self.collect()

        self.processing = {
            "nextOrder": None,
            "ordersWithError": set()
        }

    def load_plugins(self):
        self.test = pyblish.logic.registered_test()
        self.processing = {
            "nextOrder": None,
            "ordersWithError": set()
        }

        collectors = []
        validators = []
        extractors = []
        conforms = []
        plugins = pyblish.api.discover()

        targets = pyblish.logic.registered_targets() or ["default"]
        plugins = pyblish.logic.plugins_by_targets(plugins, targets)

        for plugin in plugins:
            if plugin.order < (pyblish.api.CollectorOrder + 0.5):
                collectors.append(plugin)
            elif plugin.order < (pyblish.api.ValidatorOrder + 0.5):
                validators.append(plugin)
            elif plugin.order < (pyblish.api.ExtractorOrder + 0.5):
                extractors.append(plugin)
            else:
                conforms.append(plugin)

        self.plugins = {
            self.PART_COLLECT: collectors,
            self.PART_VALIDATE: validators,
            self.PART_EXTRACT: extractors,
            self.PART_CONFORM: conforms
        }

        self.was_discovered.emit()

    def on_collected(self):
        self.was_reset.emit()

    def on_validated(self):
        pyblish.api.emit("validated", context=self.context)
        self.was_validated.emit()
        self.validated = True
        if self.publishing:
            self.extract()

    def on_extracted(self):
        self.extracted = True
        if self.publishing:
            self.publish()

    def on_published(self):
        self.was_finished.emit()
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

    def _pair_yielder(self, plugins):

        for plugin in plugins:
            if not plugin.active:
                pyblish.logic.log.debug("%s was inactive, skipping.." % plugin)
                continue

            self.processing["nextOrder"] = plugin.order

            message = self.test(**self.processing)
            if message:
                raise pyblish.logic.StopIteration("Stopped due to %s" % message)

            if not self.is_running:
                raise StopIteration("Stopped")

            if plugin.__instanceEnabled__:
                instances = pyblish.logic.instances_by_plugin(
                    self.context, plugin
                )
                for instance in instances:
                    if instance.data.get("publish") is False:
                        pyblish.logic.log.debug(
                            "%s was inactive, skipping.." % instance
                        )
                        continue
                    yield plugin, instance
            else:
                families = util.collect_families_from_instances(
                    self.context, only_active=True
                )
                plugins = pyblish.logic.plugins_by_families([plugin,], families)
                if not plugins:
                    continue
                yield plugin, None

    def iterate_and_process(
        self, plugins, on_finished=lambda: None
    ):
        """ Iterating inserted plugins with current context.
        Collectors do not contain instances, they are None when collecting!
        This process don't stop on one
        """
        def on_next():
            if self.current_pair == (None, None):
                return util.defer(100, on_finished_)
            self.about_to_process.emit(*self.current_pair)
            util.defer(100, on_process)

        def on_process():
            try:
                result = self._process(*self.current_pair)

                if result["error"] is not None:
                    self.current_error = result["error"]

                self.was_processed.emit(result)
            except Exception:
                exc_type, exc_msg, exc_tb = sys.exc_info()
                return util.defer(
                    500, lambda: on_unexpected_error(error=exc_msg)
                )
            try:
                self.current_pair = next(self.pair_generator)

            except StopIteration as e:
                # All pairs were processed successfully!
                self.current_pair = (None, None)
                return util.defer(500, on_finished_)

            except Exception as e:
                # This is a bug
                exc_type, exc_msg, exc_tb = sys.exc_info()
                self.current_pair = (None, None)
                return util.defer(
                    500, lambda: on_unexpected_error(error=exc_msg)
                )

            util.defer(10, on_next)

        def on_unexpected_error(error):
            util.u_print(u"An unexpected error occurred:\n %s" % error)
            return util.defer(500, on_finished_)

        def on_finished_():
            ''' if `self.is_running` is False then processing was stopped by
            Stop button so we do not want to execute on_finish method!
            '''
            if self.is_running:
                on_finished()

        self.is_running = True
        self.pair_generator = self._pair_yielder(plugins)
        self.current_pair = next(self.pair_generator, (None, None))
        util.defer(10, on_next)

    def collect(self):
        """ Iterate and process Collect plugins
        - load_plugins method is launched again when finished
        """
        self.iterate_and_process(
            self.plugins[self.PART_COLLECT], self.on_collected
        )

    def validate(self):
        """ Iterate and process Validate plugins
        - self.validated is set to True when done so we know was processed
        """
        self.iterate_and_process(
            self.plugins[self.PART_VALIDATE], self.on_validated
        )

    def extract(self):
        """ Iterate and process Extract plugins
        """
        if not self.validated:
            self.validate()
            return
        if self.current_error:
            self.on_published()
            return

        self.iterate_and_process(
            self.plugins[self.PART_EXTRACT], self.on_extracted
        )

    def publish(self):
        """ Iterate and process Conform(Integrate) plugins
        - won't start if any extractor fails
        """
        self.publishing = True
        if not self.extracted:
            self.extract()
            return
        if self.current_error:
            self.on_published()
            return

        self.iterate_and_process(
            self.plugins[self.PART_CONFORM], self.on_published
        )

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
