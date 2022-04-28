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
from common import Singleton


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
        }

    def cb_select_room(self, proto:dict) -> None:
        pass

    def cb_set_name(self, proto:dict) -> None:
        self.nick_name = proto["name"]
        rsp = {
            "id": PROTO.S_SET_NAME_RES,
            "errcode": ECODE.success
        }
        self.net_packet_mgr.send_proto(rsp)

    def notify_room_list(self) -> bool:
        rooms_info = g_svr.room_mgr.get_room_dict()
        ntf = {
            "id": PROTO.S_ROOM_LIST_NOTIFY,
            "rooms_info": rooms_info,
        }
        self.net_packet_mgr.send_proto(ntf)


class Room(object):
    """single chat room."""
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

    def get_room_dict(self) -> dict:
        info = {}
        for room_id, room in self.rooms:
            info[room_id] = room.nodes_num()
        return info

    def node_join_room(self, room_id:int, node:Node) -> bool:
        if room_id not in self.rooms:
            return False
        room:Room = self.rooms[room_id]
        ok = room.deal_join(node)
        if not ok:
            return False
        self.node_room_map[node.node_id] = room
        return True

@Singleton
class Server(object):
    def __init__(self) -> None:
        self.conf = Config()
        self.node_map = {} # k:v = cli_socket:Node
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
            node_id = self.id_mgr.distribute_node_id()
            new_node = Node(node_id, cli_sock, cli_addr)
            self.node_map[cli_sock] = new_node
            self.send_room_list_to_cli(new_node)
        except Exception as e:
            logging.error(e)

    def read_cli_msg(self, cli_sock:socket.socket, mask):
        print(cli_sock)
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


g_svr = Server()
g_svr.start()

    
