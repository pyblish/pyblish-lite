from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import sys

from .vendor.Qt import QtCore
from .vendor.six import text_type

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


def plugin_active_for_instance(plugin, instance):
    """Return whether `plugin` is active for `instance`."""
    if instance is None or not getattr(plugin, "__instanceEnabled__", False):
        return getattr(plugin, "active", True)

    overrides = instance.data.get("plugins", {})
    if plugin.id in overrides:
        return overrides[plugin.id]

    return getattr(plugin, "active", True)


def set_plugin_active_for_instance(plugin, instance, active):
    """Enable or disable `plugin` for `instance`."""
    if instance is None or not getattr(plugin, "__instanceEnabled__", False):
        plugin.active = active
        return

    instance.data.setdefault("plugins", {})[plugin.id] = active


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
        return QtCore.QTimer.singleShot(int(delay), func)
    else:
        return func()


def u_print(msg, **kwargs):
    """`print` with encoded unicode.

    `print` unicode may cause UnicodeEncodeError
    or non-readable result when `PYTHONIOENCODING` is not set.
    this will fix it.

    Arguments:
        msg (unicode): Message to print.
        **kwargs: Keyword argument for `print` function.
    """
    if os.getenv('PYBLISH_DISABLE_IO_ENCODING', 'no').lower() != 'yes':
        if isinstance(msg, text_type):
            try:
                encoding = sys.stdout.encoding
            except AttributeError:
                # `sys.stdout.encoding` may not exists.
                encoding = None
            encoding = os.getenv('PYTHONIOENCODING', encoding)
            msg = msg.encode(encoding or 'utf-8', 'replace')
    print(msg, **kwargs)
