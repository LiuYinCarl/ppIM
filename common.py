import socket
import time


def get_str_time():
    return "[{}]".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


def tprint(s):
    t = get_str_time()
    print("{} {}".format(t, s))


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip
