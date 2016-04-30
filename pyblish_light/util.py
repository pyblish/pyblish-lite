from Qt import QtCore

_async_threads = []


def async(target, args=None, kwargs=None, callback=None):
    """Perform operation in thread with callback

    Instances are cached until finished, at which point
    they are garbage collected. If we didn't do this,
    Python would step in and garbage collect the thread
    before having had time to finish, resulting in an
    exception.

    Arguments:
        target (callable): Method or function to call
        callback (callable, optional): Method or function to call
            once `target` has finished.

    Returns:
        None

    """

    obj = _Async(target, args, kwargs, callback)
    obj.finished.connect(lambda: _async_threads.remove(obj))
    obj.start()
    _async_threads.append(obj)
    return obj


class _Async(QtCore.QThread):
    done = QtCore.Signal("QVariant")

    def __init__(self, target, args=None, kwargs=None, callback=None):
        super(_Async, self).__init__()

        self.args = args or list()
        self.kwargs = kwargs or dict()
        self.target = target
        self.callback = callback

        if callback:
            connection = QtCore.Qt.BlockingQueuedConnection
            self.done.connect(self.callback, type=connection)

    def run(self, *args, **kwargs):
        try:
            result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            return self.done.emit(e)
        else:
            self.done.emit(result)
