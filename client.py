# from socket import *
import logging
import socket
import time
import threading
import selectors

# from common import get_host_ip
from config import Config
from network import NetPacketMgr
from proto import PROTO, ECODE
from common import get_str_time

logging.basicConfig(level=logging.DEBUG)

class Client(object):
    def __init__(self):
        self.conf = Config()
        self.sock = socket.socket()
        self.net_packet_mgr = NetPacketMgr(self.sock)
        self.proto_map = {}
        self.select_room_finsh = False
        self.server_room_list = []
        self.sel = selectors.DefaultSelector()

        self._regist_proto()


    def _dispatch(self, proto:dict) -> None:
        proto_id = proto["id"]
        if proto_id not in self.proto_map:
            logging.error("unknown proto_id({})".format(proto_id))
            logging.error("proto_id: {}".format(self.proto_map.keys()))
            return
        cb_func = self.proto_map[proto_id]
        cb_func(proto)

    def _regist_proto(self):
        self.proto_map = {
            PROTO.S_ROOM_LIST_NOTIFY : self.cb_room_list_notify,
            PROTO.S_SELECT_ROOM_RES: self.cb_select_room,
            PROTO.S_SET_NAME_RES : self.cb_set_name,
            PROTO.S_MSG_NOTIFY: self.cb_msg_notify,
        }

    def cb_room_list_notify(self, proto:dict) -> None:
        rooms_info = proto["rooms_info"]
        print(rooms_info)
        self.server_room_list = [int(id) for id in rooms_info.keys()]
        print(self.server_room_list)
        print("select a room enter:")
        tmp = ""
        n = 0
        for room_id, node_cnt in rooms_info.items():
            tmp += "房间:{} ({}人)".format(room_id, node_cnt)
            n += 1
            if n % 5 == 0:
                tmp += "\n"
        print(tmp)

    def cb_select_room(self, proto:dict) -> None:
        errcode = proto["errcode"]
        if errcode != ECODE.success:
            logging.error("select room failed. errcode:{}".format(errcode))
            return
        self.select_room_finsh = True

    def cb_set_name(self, proto:dict) -> None:
        errcode = proto["errcode"]
        if errcode != ECODE.success:
            logging.error("set name failed. errcode:{}".format(errcode))

    def cb_msg_notify(self, proto:dict) -> None:
        msg = proto["msg"]
        print(msg)

    def set_name_req(self, name:str) -> bool:
        if not isinstance(name, str):
            logging.error("name is not str.")
            return False
        if not name:
            logging.warn("name is empty.")
            return False
        req = {
            "id": PROTO.C_SET_NAME_REQ,
            "nick_name": name,
        }
        self.net_packet_mgr.send_proto(req)

    def select_room(self, room_id:int):
        if room_id not in self.server_room_list:
            logging.error("input not exist room id.")
            return
        req = {
            "id": PROTO.C_SELECT_ROOM_REQ,
            "room_id": room_id,
        }
        self.net_packet_mgr.send_proto(req)

    def msg_send(self, msg):
        req = {
            "id": PROTO.C_SEND_MSG_REQ,
            "msg": msg,
        }
        self.net_packet_mgr.send_proto(req)

    def listen_input(self):
        while True:
            if not self.select_room_finsh:
                s = input("select room id:")
                try:
                    room_id = int(s)
                    self.select_room(room_id)
                except Exception:
                    print("enter weong. please select a room id.")
            else:
                s = input("{} >>> ".format(get_str_time()))
                self.msg_send(s)

    def read_svr(self, sock:socket.socket, mask):
        proto = self.net_packet_mgr.recv_proto()
        self._dispatch(proto)

    def listen_server(self):
        try:
            self.sock.connect((self.conf.server_ip, self.conf.server_port))
            self.sock.setblocking(False)
            self.sel.register(self.sock, selectors.EVENT_READ, self.read_svr)
        except Exception as e:
            print("conn to server failed. err:{}".format(e))
            self.sock.close()
            return

        self.set_name_req("Jim")

        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

    def start(self):
        # self.listen_server()

        svr_thread = threading.Thread(None, self.listen_server)
        svr_thread.start()

        input_thread = threading.Thread(None, self.listen_input)
        input_thread.start()

        svr_thread.join()
        input_thread.join()

if __name__ == '__main__':
    cli = Client()
    cli.start()
