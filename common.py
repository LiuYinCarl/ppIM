import time


def get_str_time():
    return "[{}]".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

def tprint(s):
    t = get_str_time()
    print("{} {}".format(t, s))