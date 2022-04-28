# from socket import *
import logging
import os
import signal
import socket
import sys

# from common import get_host_ip
from config import Config
from network import NetPacketMgr
from proto import PROTO, ECODE

logging.basicConfig(level=logging.DEBUG)

class Client(object):
    def __init__(self):
      self.conf = Config()
      self.sock = socket.socket()
      self.net_packet_mgr = NetPacketMgr(self.sock)
      self.proto_map = {}
      self._regist_proto()


    def _dispatch(self, proto:dict) -> None:
        proto_id = proto["id"]
        if proto_id not in self.proto_map:
            logger.error("unknown proto_id({})".format(proto_id))
            logger.error("proto_id: {}".format(self.proto_map.keys()))
            return
        cb_func = self.proto_map[proto_id]
        cb_func(proto)

    def _regist_proto(self):
        self.proto_map = {
            PROTO.S_ROOM_LIST_NOTIFY : self.cb_room_list_notify,
            PROTO.S_SELECT_ROOM_RES: self.cb_select_room,
            PROTO.S_SET_NAME_RES : self.cb_set_name,
        }

    def cb_room_list_notify(self, proto:dict) -> None:
        pass

    def cb_select_room(self, proto:dict) -> None:
        pass

    def cb_set_name(self, proto:dict) -> None:
        errcode = proto["errcode"]
        if errcode != ECODE.success:
            logger.error("set name failed. errcode:{}".format(errcode))

    def set_name_req(self, name:str) -> bool:
        if not isinstance(name, str):
            logger.error("name is not str.")
            return False
        if not name:
            logger.warn("name is empty.")
            return False
        req = {
            "id": PROTO.C_SET_NAME_REQ,
            "nick_name": name,
        }
        self.net_packet_mgr.send_proto(req)


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
            self.sock.connect((self.conf.server_ip, self.conf.server_port))
        except Exception as e:
            print("conn to serer failed. err:{}".format(e))
            self.sock.close()
            return

        self.set_name_req("Jim")

        while True:
            proto = self.net_packet_mgr.recv_proto()
            self._dispatch(proto)


if __name__ == '__main__':
    cli = Client()
    cli.start()
