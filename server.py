# server 启动的时候生成一个随机密钥
# server 在 client 连接上来的时候用兑成加密算法发送随机密钥给客户端
# 之后客户端和服务端使用随机密钥加密信息进行通信
#

from cmath import log
from msilib import init_database
import os
import logging
import sys
import time
import socket
import selectors
from threading import Thread
from unicodedata import name
from config import Config
from common import get_str_time, tprint

node_id = 0
def distribute_node_id():
    id = node_id
    node_id += 1
    return id

class IdMgr(object):
    def __init__(self) -> None:
        self._node_id = 0
        self._room_id = 0

    def distribute_node_id(self):
        id = self._node_id
        self._node_id += 1
        return id

    def distribute_room_id(self):
        id = self._room_id
        self._room_id += 1
        return id
    

class Node():
    """single user info."""
    def __init__(self, node_id, socket, addr):
        self.node_id = node_id
        self.socket = socket
        self.addr = addr
        self.close_flag = False

        self.name = None # 用户名
        self.room_id = None # 用户所在的房间
        self.recv_msg_list = []
        self.send_msg_list = []

    def send(self, msg):
        """send message to client."""
        msg = msg.encode("utf8")
        self.send_msg_list.append(msg)
        logging.debug("user:{} room:{} send:{}".format(self.name, self.room, msg))

    def recv(self, msg):
        """receive message from client."""
        data = self.socket.recv(1024)
        if not data:
            self.close_flag = True
            logging.info("client close.")
            return
        msg = data.decode("utf8")
        self.recv_msg_list.append(msg)
        logging.debug("user:{} room:{} recv:{}".format(self.name, self.room, msg))

class Room(object):
    """一个房间."""
    def __init__(self, id):
        self.room_id = id
        self.nodes = {}

    def uninit(self):
        # TODO send server down to all node.
        logging.info("room({}) destroy.".format(self.room_id))

    def deal_join(self, node):
        """manager user join room."""
        pass

    def deal_leave(self):
        """manager user leave room."""
    
    def recv(self):
        """room reveive message come from user."""
        pass

    def send(self):
        """room send message to all."""
        pass

    def update(self):
        """update the room."""
        pass

    def nodes_num(self):
        return len(self.nodes)

class RoomMgr(object):
    """room manager."""
    def __init__(self) -> None:
        self._room_id = 0
        self.rooms = {}
        self.node_room_map = {}

    def create_room(self):
        id = self.distribute_room_id()
        if id in self.rooms:
            logging.error("duplicated room id")
            return
        new_room = Room(id)
        self.rooms[id] = new_room

    def destroy_room(self, id):
        if id not in self.rooms:
            logging.error("room({}) not exist.".format(id))
            return
        room = self.rooms[id]
        room.uninit()

    def update(self):
        for room in self.rooms.items():
            room.update()

    def distribute_room_id(self):
        id = self._room_id
        self._room_id += 1
        return id

    def get_room_list(self):
        info = []
        for room_id, room in self.rooms:
            info.append([room_id, room.nodes_num()])
        return info

    def node_join_room(self, room_id:int, node:Node) -> bool:
        if room_id not in self.rooms:
            return False
        room:Room = self.rooms[room_id]
        ok = room.deal_join(node)
        if not ok:
            return False
        self.node_room_map[node.]
        return True


class Server(object):
    def __init__(self) -> None:
        self.conf = Config()
        self.node_map = {} # cli_sock:Node
        self.room_mgr = RoomMgr()
        self.id_mgr = IdMgr()
        self.svr_socket = socket.socket()
        self.wait_node_list = [] # users still not enter a room
        self.sel = selectors.DefaultSelector()

    def send_room_list_to_cli(self, node:Node):
        room_info = self.room_mgr.get_room_list()
        node.send(room_info) # TODO room_info need to be string
        self.wait_node_list.append(node)

    def deal_wait_node_list(self):
        need_delete_node = []
        for node in self.wait_node_list:
            msg = node.recv()
            # at there, we only accept select room cmd
            if "select_room" not in msg:
                logging.error("error message. only accept select room cmd.")
                continue
            except_room_id = int(msg.split(" ")[-1])
            ok = self.room_mgr.node_join_room(except_room_id, node)
            if ok == True:
                need_delete_node.append(node)
        for node in need_delete_node:
            self.wait_node_list.remove(node)

    def init_svr_socket(self):
        self.svr_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.svr_socket.bind(self.conf.server_port)
        self.svr_socket.listen(100)
        self.svr_socket.setblocking(False)
        self.sel.register(self.svr_socket, selectors.EVENT_READ, self.accept_cli)
        logging.info("ppIM Server wait connect.")

    def accept_cli(self, server_sock, mask):
        try:
            # server_sock = self.svr_socket
            cli_sock, cli_addr = self.svr_socket.accept()
            cli_sock.setblocking(False)
            self.sel.register(cli_sock, selectors.EVENT_READ, self.read_cli_msg)
            node_id = self.id_mgr.distribute_node_id()
            new_node = Node(node_id, cli_sock, cli_addr)
            self.send_room_list_to_cli(new_node)
        except Exception as e:
            logging.error(e)

    def read_cli_msg(self, cli_sock, mask):
        node:Node = self.node_map(cli_sock)
        node.recv()

    def start(self):
        self.init_svr_socket()
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)


if __name__ == "__main__":
    svr = Server()
    svr.start()
