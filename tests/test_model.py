import logging

# Vendor libraries
from nose.tools import (
    with_setup,
)

import pyblish.api
from pyblish_lite import model
from pyblish_lite.vendor import six


def clean():
    pyblish.api.deregister_all_plugins()


def test_label_nonstring():
    """Logging things that aren't string is fine"""

    result = {
        "records": [
            logging.LogRecord("root", "INFO", "", 0, msg, [], None)
            for msg in (
                "Proper message",
                12,
                {"a": "dict"},
                list(),
                1.0,
            )
        ],
        "error": None
    }

    model_ = model.Terminal()
    model_.update_with_result(result)

    for item in model_:
        assert isinstance(item.data(model.Label), six.text_type), (
            "\"%s\" wasn't a string!" % item.data(model.Label))


@with_setup(clean)
def test_proxy_hideinactive():
    """Plug-ins without active instances are hidden"""

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