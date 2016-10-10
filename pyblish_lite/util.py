import os

from .vendor.Qt import QtCore

root = os.path.dirname(__file__)


def get_asset(*path):
    """Return path to asset, relative the install directory

    Usage:
        >>> path = get_asset("dir", "to", "asset.png")
        >>> path == os.path.join(root, "dir", "to", "asset.png")
        True

    Arguments:
        path (str): One or more paths, to be concatenated

    """

    return os.path.join(root, *path)


def defer(delay, func):
    """Append artificial delay to `func`

    This aids in keeping the GUI responsive, but complicates logic
    when producing tests. To combat this, the environment variable ensures
    that every operation is synchonous.

    Arguments:
        delay (float): Delay multiplier; default 1, 0 means no delay
        func (callable): Any callable

    """

    delay *= float(os.getenv("PYBLISH_DELAY", 1))
    if delay > 0:
        return QtCore.QTimer.singleShot(delay, func)
    else:
        return func()
