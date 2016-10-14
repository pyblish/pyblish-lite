import pyblish.api
import pyblish.lib
from pyblish_lite import control

# Vendor libraries
from nose.tools import (
    with_setup,
    assert_equals
)


def clean():
    pyblish.api.deregister_all_plugins()


@with_setup(clean)
def test_something():
    """Anything runs"""
    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_plugin(MyCollector)

    ctrl = control.Controller()
    ctrl.reset()

    assert count["#"] == 1


@with_setup(clean)
def test_logging_nonstring():
    """Logging things that aren't string is fine"""
    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            self.log.info({"A dictionary is": "fine"})
            self.log.info(12)
            self.log.info(True)
            self.log.info(1.0)
            self.log.info(["a list"])
            self.log.info(("a", "list"))
            self.log.info(set(["a", "list"]))
            count["#"] += 1

    pyblish.api.register_plugin(MyCollector)

    ctrl = control.Controller()
    ctrl.reset()

    assert count["#"] == 1


@with_setup(clean)
def test_reset():
    """Resetting works the way you'd expect"""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("MyInstance")
            count["#"] += 1

    class MyValidator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            count["#"] += 11

    for plugin in [MyCollector, MyValidator]:
        pyblish.api.register_plugin(plugin)

    ctrl = control.Controller()
    ctrl.reset()

    assert count["#"] == 1


@with_setup(clean)
def test_publish():
    """Publishing works the way you'd expect"""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("MyInstance")
            print(type(self))
            count["#"] += 1

    class MyValidator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            print(type(self))
            count["#"] += 10

    for plugin in [MyCollector, MyValidator]:
        pyblish.api.register_plugin(plugin)

    ctrl = control.Controller()
    ctrl.reset()

    assert count["#"] == 1, count

    ctrl.publish()

    assert count["#"] == 11, count

    # There are no more items in the queue at this point,
    # so publishing again should do nothing.
    ctrl.publish()

    assert count["#"] == 11, count


@with_setup(clean)
def test_publish_families():
    """Only supported families are published"""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("MyInstance", families=["myFamily"])
            print(type(self))
            count["#"] += 1

    class Supported(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        families = ["myFamily"]

        def process(self, instance):
            print(type(self))
            count["#"] += 10

    class Unsupported(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder
        families = ["unsupported"]

        def process(self, instance):
            print(type(self))
            count["#"] += 100

    for plugin in [MyCollector, Supported, Unsupported]:
        pyblish.api.register_plugin(plugin)

    ctrl = control.Controller()
    ctrl.reset()

    assert count["#"] == 1, count

    ctrl.publish()

    assert count["#"] == 11, count


@with_setup(clean)
def test_publish_inactive():
    """Only active plugins are published"""

    count = {"#": 0}

    class Active(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            print(type(self))
            count["#"] += 1

    class Inactive(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder
        active = False

        def process(self, context):
            print(type(self))
            count["#"] += 10

    for plugin in [Active, Inactive]:
        pyblish.api.register_plugin(plugin)

    ctrl = control.Controller()
    ctrl.reset()

    assert count["#"] == 1, count


@with_setup(clean)
def test_publish_disabled():
    """Only active instances are published"""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            context.create_instance("A", publish=False)
            context.create_instance("B", publish=True)
            count["#"] += 1

    class MyValidator(pyblish.api.InstancePlugin):
        order = pyblish.api.ValidatorOrder

        def process(self, instance):
            count["#"] += 10

    for plugin in [MyCollector, MyValidator]:
        pyblish.api.register_plugin(plugin)

    ctrl = control.Controller()
    ctrl.reset()

    assert count["#"] == 1, count

    ctrl.publish()

    assert count["#"] == 11, count


@with_setup(clean)
def test_order_20():
    """Orders beyond CVEI should still run"""

    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.data["families"] = ["myFamily"]
            count["#"] += 1

    class OldValidator(pyblish.api.Validator):
        """Old-style plug-in, not using InstancePlugin"""

        families = ["myFamily"]
        order = 20

        def process(self, instance):
            count["#"] += 10

    class NewValidator(pyblish.api.InstancePlugin):
        families = ["myFamily"]
        order = 20

        def process(self, instance):
            count["#"] += 100

    pyblish.api.register_plugin(MyCollector)
    pyblish.api.register_plugin(OldValidator)
    pyblish.api.register_plugin(NewValidator)

    ctrl = control.Controller()
    ctrl.reset()

    assert count["#"] == 1, count

    ctrl.publish()

    assert count["#"] == 111, count


@with_setup(clean)
def test_far_negative_orders():
    """Orders may go below 0"""

    count = {"#": 0}

    class MyCollector1(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

    class MyCollector2(pyblish.api.ContextPlugin):
        order = -1

    class MyCollector3(pyblish.api.ContextPlugin):
        order = -1000

    def process(self, context):
        count["#"] += 1

    MyCollector1.process = process
    MyCollector2.process = process
    MyCollector3.process = process

    pyblish.api.register_plugin(MyCollector1)
    pyblish.api.register_plugin(MyCollector2)
    pyblish.api.register_plugin(MyCollector3)

    ctrl = control.Controller()
    ctrl.reset()

    # They all register as Collectors
    assert count["#"] == 3, count


def test_controller_signals():
    """was_finished emitted on completing any process

    Any process, such as resetting, validating,
    actuating and publishing.

    """

    count = {
        "was_reset": 0,
        "was_validated": 0,
        "was_published": 0,
        "was_finished": 0,
    }

    def on_signal(signal):
        count[signal] += 1

    ctrl = control.Controller()

    ctrl.was_reset.connect(lambda: on_signal("was_reset"))
    ctrl.was_validated.connect(lambda: on_signal("was_validated"))
    ctrl.was_published.connect(lambda: on_signal("was_published"))
    ctrl.was_finished.connect(lambda: on_signal("was_finished"))

    ctrl.reset()

    assert_equals(count, {
        "was_reset": 1,
        "was_validated": 0,
        "was_published": 0,
        "was_finished": 1,
    })

    ctrl.validate()

    assert_equals(count, {
        "was_reset": 1,
        "was_validated": 1,
        "was_published": 0,
        "was_finished": 2,
    })

    ctrl.publish()

    assert_equals(count, {
        "was_reset": 1,
        "was_validated": 1,
        "was_published": 1,
        "was_finished": 3,
    })
