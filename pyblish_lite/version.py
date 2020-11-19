
VERSION_MAJOR = 0
VERSION_MINOR = 8
VERSION_PATCH = 8
VERSION_BETA = "b2"

version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, VERSION_BETA)
version = '%i.%i.%i%s' % version_info
__version__ = version

__all__ = ['version', 'version_info', '__version__']
