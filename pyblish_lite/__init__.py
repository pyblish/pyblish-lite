VERSION_MAJOR = 0
VERSION_MINOR = 3
VERSION_PATCH = 0

version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
version = '%i.%i.%i' % version_info
__version__ = version

from . import compat as __compat
__compat.init()

from .app import show

__all__ = [
    'show',
    'version',
    'version_info',
    '__version__'
]
