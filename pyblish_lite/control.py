"""The Controller in a Model/View/Controller-based application

The graphical components of Pyblish Lite use this object to perform
publishing. It communicates via the Qt Signals/Slots mechanism
and has no direct connection to any graphics. This is important,
because this is how unittests are able to run without requiring
an active window manager; such as via Travis-CI.

"""

import traceback

from .vendor.Qt import QtCore

import pyblish.api
import pyblish.lib
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

    def __init__(self, parent=None):
        super(Controller, self).__init__(parent)

        self.context = list()
        self.plugins = list()

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
        self.context = pyblish.api.Context()
        self.plugins = pyblish.api.discover()

        self.was_discovered.emit()

        self.pair_generator = None
        self.current_pair = (None, None)
        self.current_error = None

        self.processing = {
            "nextOrder": None,
            "ordersWithError": set()
        }

        self._load()
        self._run(until=pyblish.api.CollectorOrder,
                  on_finished=self.was_reset.emit)

    def validate(self):
        # The iterator doesn't sync with the GUI check states so
        # reset the iterator to ensure we grab the updated instances
        # assuming the plugins are already sorted from api.Discover()
        self._reset_iterator(start_from=pyblish.api.ValidatorOrder)
        self._run(until=pyblish.api.ValidatorOrder,
                  on_finished=self.on_validated)

    def publish(self):
        plugin = self.current_pair[0]
        if plugin:
            # The iterator doesn't sync with the GUI check states so
            # reset the iterator to ensure we grab the updated instances
            self._reset_iterator(start_from=plugin.order, subtract_offset=False)
        self._run(on_finished=self.on_published)

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

    def _load(self):
        """Initiate new generator and load first pair"""
        self.is_running = True
        self.pair_generator = self._iterator(self.plugins,
                                             self.context)
        self.current_pair = next(self.pair_generator, (None, None))
        self.current_error = None
        self.is_running = False

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
            raise Exception("Unknown error: %s" % e)

        else:
            # Make note of the order at which the
            # potential error error occured.
            has_error = result["error"] is not None
            if has_error:
                self.processing["ordersWithError"].add(plugin.order)

        return result

    def _run(self, until=float("inf"), on_finished=lambda: None):
        """Process current pair and store next pair for next process

        Arguments:
            until (pyblish.api.Order, optional): Keep fetching next()
                until this order, default value is infinity.
            on_finished (callable, optional): What to do when finishing,
                defaults to doing nothing.

        """

        def on_next():
            if self.current_pair == (None, None):
                return util.defer(100, on_finished_)

            # The magic number 0.5 is the range between
            # the various CVEI processing stages;
            # e.g.
            #  - Collection is 0 +- 0.5 (-0.5 - 0.5)
            #  - Validation is 1 +- 0.5 (0.5  - 1.5)
            #
            # TODO(marcus): Make this less magical
            #
            order = self.current_pair[0].order
            if order > (until + 0.5):
                return util.defer(100, on_finished_)

            # The instance may have been disabled, check because the iterator will
            # have already provided it
            if self._current_pair_is_active():
                self.about_to_process.emit(*self.current_pair)

            util.defer(10, on_process)

        def on_process():
            try:
                if self._current_pair_is_active():
                    result = self._process(*self.current_pair)

                    if result["error"] is not None:
                        self.current_error = result["error"]

                    self.was_processed.emit(result)

            except Exception as e:
                stack = traceback.format_exc()
                return util.defer(
                    500, lambda: on_unexpected_error(error=stack))

            # Now that processing has completed, and context potentially
            # modified with new instances, produce the next pair.
            #
            # IMPORTANT: This *must* be done *after* processing of
            # the current pair, otherwise data generated at that point
            # will *not* be included.
            try:
                self.current_pair = next(self.pair_generator)

            except StopIteration:
                # All pairs were processed successfully!
                self.current_pair = (None, None)
                return util.defer(500, on_finished_)

            except Exception as e:
                # This is a bug
                stack = traceback.format_exc()
                self.current_pair = (None, None)
                return util.defer(
                    500, lambda: on_unexpected_error(error=stack))

            util.defer(10, on_next)

        def on_unexpected_error(error):
            util.u_print(u"An unexpected error occurred:\n %s" % error)
            return util.defer(500, on_finished_)

        def on_finished_():
            on_finished()
            self.was_finished.emit()

        self.is_running = True
        util.defer(10, on_next)

    def _current_pair_is_active(self):
        return self.current_pair[1] is None or self.current_pair[1].data.get("publish", True)

    def _reset_iterator(self, start_from=-float("inf"), subtract_offset=True):
        # In most cases when passed the int value of an order, we need to subtract
        # 0.5, because each order is a range of values, from -0.5 to 0.5.
        # E.g. ExtractorOrder is 2, and spans between 1.5-2.5
        start_from = start_from - 0.5 if subtract_offset else start_from
        self.is_running = True
        self.pair_generator = self._iterator(
            self.plugins,
            self.context,
            start_from
        )

        self.current_pair = next(self.pair_generator, (None, None))
        self.is_running = False

    def _iterator(self, plugins, context, start_from=-float("inf")):
        """Yield next plug-in and instance to process.

        Arguments:
            plugins (list): Plug-ins to process
            context (pyblish.api.Context): Context to process

        """
        test = pyblish.logic.registered_test()

        for plug, instance in pyblish.logic.Iterator(plugins, context):
            order = plug.order

            if order < start_from or not plug.active:
                continue

            if instance is not None and instance.data.get("publish") is False:
                continue

            self.processing["nextOrder"] = plug.order

            if not self.is_running:
                raise StopIteration("Stopped")

            if test(**self.processing):
                raise StopIteration("Stopped due to %s" % test(
                    **self.processing))

            yield plug, instance

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
