# from socket import *
import os
import signal
import socket
import sys

from common import get_host_ip
from config import Config


class Client(object):
    def __init__(self):
      self.conf = Config()
      self.sockfd = socket.socket()
      self.local_ip = get_host_ip()

    def _send(self, msg):
        self.sockfd.send(msg)

    def _recv(self):
        data = self.sockfd.recv(1024)
        return data

    def msg_recv(self):
        while True:
            data = self._recv()
            msg = data.decode("utf8")
            if msg == "exit":
                print("client exit")
                break
            print(msg)

    def msg_send(self):
        while True:
            data = input()
            msg = data.encode("utf8")
            self._send(msg)
            if msg == "exit":
                break

    def start(self):
        try:
            self.sockfd.connect((self.conf.server_ip, self.conf.server_port))
        except Exception as e:
            print("conn to serer failed. err:{}".format(e))
            self.sockfd.close()
            return

        while True:
            self._send("client({}) join.".format(self.local_ip))
            data = self._recv()
            msg = data.decode("utf8")
            if msg == "ok":
                print("enter im success.")
                break
            else:
                print("enter im failed. err({})".format(msg))

        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        pid = os.fork()

        if pid < 0:
            sys.exit("err")
        elif pid == 0:
            self.msg_recv()
        else:
            print("main thread pid:{}".format(pid))
            self.msg_send()


if __name__ == '__main__':
    cli = Client()
    cli.start()
