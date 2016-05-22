import logging

from pyblish_lite import model
from pyblish_lite.vendor import six


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
