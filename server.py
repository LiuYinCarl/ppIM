# server 启动的时候生成一个随机密钥
# server 在 client 连接上来的时候用兑成加密算法发送随机密钥给客户端
# 之后客户端和服务端使用随机密钥加密信息进行通信
#
import logging
import socket
import selectors
from config import Config
from network import NetPacketMgr
from proto import PROTO, ECODE
from common import Singleton, get_str_time

logging.basicConfig(level=logging.DEBUG)


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
    def __init__(self, node_id, cli_socket, addr):
        self.node_id = node_id
        self.socket = cli_socket
        self.addr = addr
        self.close_flag = False
        self.proto_map = {}

        self.nick_name = None # client user nick name
        self.room_id = None # the room which node in
        self.net_packet_mgr = NetPacketMgr(cli_socket)

        self._register_proto()

    def send(self, proto):
        """send message to client."""
        self.net_packet_mgr.send_proto(proto)

    def recv(self):
        """receive message from client."""
        proto = self.net_packet_mgr.recv_proto()
        self._dispatch(proto)

    def _dispatch(self, proto:dict) -> None:
        proto_id = proto["id"]
        if proto_id not in self.proto_map:
            logging.error("unknown proto_id({})".format(proto_id))
            return
        cb_func = self.proto_map[proto_id]
        cb_func(proto)

    def _register_proto(self):
        self.proto_map = {
            PROTO.C_SELECT_ROOM_REQ : self.cb_select_room, 
            PROTO.C_SET_NAME_REQ : self.cb_set_name,
            PROTO.C_SEND_MSG_REQ: self.cb_msg_req,
        }

    def cb_select_room(self, proto:dict) -> None:
        room_id = proto["room_id"]
        ok = g_svr.room_mgr.node_join_room(room_id, self)
        if ok:
            self.room_id = room_id

        rsp = {
            "id": PROTO.S_SELECT_ROOM_RES,
            "errcode": ECODE.success if ok else ECODE.join_room_failed,
        }
        self.net_packet_mgr.send_proto(rsp)

    def cb_set_name(self, proto:dict) -> None:
        self.nick_name = proto["nick_name"]
        rsp = {
            "id": PROTO.S_SET_NAME_RES,
            "errcode": ECODE.success
        }
        self.net_packet_mgr.send_proto(rsp)
        
        self.notify_room_list()

    def cb_msg_req(self, proto:dict) -> None:
        msg = "{} {}: {}".format(get_str_time(), self.nick_name, proto["msg"])
        room:Room = g_svr.room_mgr.get_room_by_id(self.room_id)
        room.broadcast_msg(msg)

    def notify_room_list(self) -> bool:
        rooms_info = g_svr.room_mgr.get_room_dict()
        ntf = {
            "id": PROTO.S_ROOM_LIST_NOTIFY,
            "rooms_info": rooms_info,
        }
        self.net_packet_mgr.send_proto(ntf)
    
    def notify_msg(self, msg:str) -> bool:
        ntf = {
            "id": PROTO.S_MSG_NOTIFY,
            "msg": msg,
        }
        self.net_packet_mgr.send_proto(ntf)


class Room(object):
    """single chat room."""
    def __init__(self, id):
        self.room_id = id
        self.nodes = {} # node_id:Node

    def uninit(self):
        # TODO send server down to all node.
        logging.info("room({}) destroy.".format(self.room_id))

    def deal_join(self, node:Node) -> bool:
        """manager user join room."""
        self.nodes[node.node_id] = node

    def deal_leave(self, node:Node) -> bool:
        """manager user leave room."""
        self.nodes.pop(node.node_id)

    def update(self):
        """update the room."""
        pass

    def is_node_in_room(self, node_id:int) -> bool:
        return node_id in self.nodes

    def nodes_num(self):
        return len(self.nodes)

    def broadcast_msg(self, msg:str) -> bool:
        for node in self.nodes.values():
            node.notify_msg(msg)
        return True

class RoomMgr(object):
    """room manager."""
    def __init__(self) -> None:
        self.rooms = {} # room_id:room
        self.node_room_map = {}

        self.create_default_room()

    def create_default_room(self):
        for _ in range(5):
            self.create_room()

    def create_room(self):
        id = g_id_mgr.distribute_room_id()
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

    def get_room_dict(self) -> dict:
        info = {}
        for room_id, room in self.rooms.items():
            info[room_id] = room.nodes_num()
        return info

    def get_room_by_id(self, room_id:int) -> Room:
        if room_id not in self.rooms:
            logging.error("room({}) not exist".format(room_id))
            return None
        return self.rooms[room_id]

    def node_join_room(self, room_id:int, node:Node) -> bool:
        if room_id not in self.rooms:
            return False
        room:Room = self.rooms[room_id]
        if not room.is_node_in_room(node.node_id):
            room.deal_join(node)
            self.node_room_map[node.node_id] = room
            return True
        return False

@Singleton
class Server(object):
    def __init__(self) -> None:
        self.conf = Config()
        self.node_map = {} # k:v = cli_socket:Node
        self.room_mgr = RoomMgr()
        # self.id_mgr = IdMgr()
        self.svr_socket = socket.socket()
        self.wait_node_list = [] # users still not enter a room
        self.sel = selectors.DefaultSelector()

    def init_svr_socket(self):
        self.svr_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.svr_socket.bind((self.conf.server_ip, self.conf.server_port))
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
            node_id = g_id_mgr.distribute_node_id()
            new_node = Node(node_id, cli_sock, cli_addr)
            self.node_map[cli_sock] = new_node
        except Exception as e:
            logging.error(e)

    def read_cli_msg(self, cli_sock:socket.socket, mask):
        node:Node = self.node_map[cli_sock]
        node.recv()

    def start(self):
        self.init_svr_socket()
        logging.info("Server start.")
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)


g_id_mgr = IdMgr()

g_svr = Server()
g_svr.start()

    
