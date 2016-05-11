import pyblish.api
from pyblish_lite import control


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
