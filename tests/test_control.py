import pyblish.api
from pyblish_lite import control

# Vendor libraries
from nose.tools import (
    with_setup
)


def clean():
    pyblish.api.deregister_all_paths()
    pyblish.api.deregister_all_plugins()


@with_setup(clean)
def test_something():
    count = {"#": 0}

    class MyCollector(pyblish.api.ContextPlugin):
        order = pyblish.api.CollectorOrder

        def process(self, context):
            count["#"] += 1

    pyblish.api.register_plugin(MyCollector)

    window = control.Window()
    window.reset()

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

    window = control.Window()
    window.reset()

    assert count["#"] == 1
