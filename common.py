import time


def get_str_time():
    return "[{}]".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


def tprint(s):
    t = get_str_time()
    print("{} {}".format(t, s))


def Singleton(cls):
    """simple and not multi-thread safe singleton."""
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton
