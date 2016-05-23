from .version import version, version_info, __version__
from . import compat as __compat

# This must be run prior to importing the application, due to the
# application requiring a discovered copy of Qt bindings.
__compat.init()

from .app import show

__all__ = [
    'show',
    'version',
    'version_info',
    '__version__'
]
