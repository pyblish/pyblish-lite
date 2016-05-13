from pyblish_lite import model
from pyblish_lite.vendor import six


def test_label_nonstring():
    """Logging things that aren't string is fine"""

    result = {
        "records": [
            type("LogRecord", (object,), {"msg": "Proper message"}),
            type("LogRecord", (object,), {"msg": 12}),
            type("LogRecord", (object,), {"msg": {"a": "dict"}}),
            type("LogRecord", (object,), {"msg": list()}),
            type("LogRecord", (object,), {"msg": 1.0}),
        ],
        "error": None
    }

    model_ = model.Terminal()
    model_.update_with_result(result)

    for item in model_:
        assert isinstance(item.data(model.Label), six.text_type), (
            "\"%s\" wasn't a string!" % item.data(model.Label))
