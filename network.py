# 一个网络包的格式
# 前 2 字节表示这个包的长度 n, 接下来的 2 字节表示这个包的内容

import base64
import json
import logging
import random
import unittest

from Crypto.Cipher import AES

PACKET_HEAD_LENGTH = 2
MAX_PACK_SIZE = (1 << 16) - 1
AES_SECRET_KEY = b"ufahdufhaiufugil"

class NetPacketMgr(object):
    def __init__(self, socket):
        self.aes = AES.new(AES_SECRET_KEY, AES.MODE_ECB)
        self.socket = socket
        self.send_packet_list = []
        self.recv_packet_list = []
        self.recv_cache = bytes()

    def _pack_header(self, packet_body_len) -> bytes:
        if packet_body_len > MAX_PACK_SIZE:
            return False, None
        head = packet_body_len.to_bytes(PACKET_HEAD_LENGTH, byteorder="big")
        return True, head
    
    def _unpack_header(self, packet_header) -> int:
        return int.from_bytes(packet_header, byteorder="big")

    def _pack_body(self, data:str) -> bytes:
        return bytes(data, encoding="utf8")

    def _unpack_body(self, packet_body:bytes) -> str:
        return str(packet_body, encoding="utf8")

    def _encrypt(self, data:str) -> str:
        data = data.encode("utf8")
        while len(data) % 16 != 0:
            data += b"\x00"
        en_data = self.aes.encrypt(data)
        return str(base64.b64encode(en_data), encoding="utf8")

    def _decrypt(self, data:str) -> str:
        data = data.encode("utf8")
        data = base64.b64decode(data)
        de_data = self.aes.decrypt(data)
        return str(de_data, encoding="utf8").strip('\0')
    
    def _pack(self, data:str):
        body = self._pack_body(data)
        header = self._pack_header(len(body))
        packet = header + body
        return packet

    def _send(self, data:str) -> bool:
        packet = self._pack(data)
        self.send_packet_list.append(packet)
        while len(self.send_packet_list) > 0:
            # TODO check if socket send is success
            self.socket.send(self.send_packet_list[0])
            self.send_packet_list.pop[0]

    def _recv(self) -> str:
        data = self.socket.recv(1024)
        self.recv_cache += data
        if len(self.recv_cache) < PACKET_HEAD_LENGTH:
            return None # still not receive a full packet header
        header = self.recv_cache[:PACKET_HEAD_LENGTH]
        body_len = self._unpack_header(header)
        if PACKET_HEAD_LENGTH + body_len > len(self.recv_cache):
            return None # still not receive a full packet
        packet_size = PACKET_HEAD_LENGTH + body_len
        body = self.recv_cache[PACKET_HEAD_LENGTH: packet_size]
        self.recv_cache = self.recv_cache[:packet_size] # remove first packet
        data = self._unpack_body(body)
        logging.debug("rece: proto:{}".format(data))
        return data

    def send_proto(self, proto:dict) -> bool:
        if proto.get("id") is None:
            logging.error("proto lost id.")
            return False
        data = json.dump(proto)
        self._send(data)
        return True

    def recv_proto(self) -> dict:
        json_str = self._recv()
        if json_str is None:
            return None
        return json.load(json_str)






class TestNetPacketMgr(unittest.TestCase):
    def get_rand_str(self):
        s = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        res = [random.choice(s) for i in range(100)]
        return "".join(res)

    def test_pack_header(self):
        netpack_mgr = NetPacketMgr()
        for packet_len in range(1, MAX_PACK_SIZE):
            ok, head = netpack_mgr._pack_header(packet_len)
            self.assertTrue(ok)
            new_packet_len = netpack_mgr._unpack_header(head)
            self.assertEqual(packet_len, new_packet_len)
    
    def test_pack_body(self):
        netpack_mgr = NetPacketMgr()
        for i in range(100):
            data = self.get_rand_str()
            packet_body = netpack_mgr._pack_body(data)
            new_data = netpack_mgr._unpack_body(packet_body)
            self.assertEqual(data, new_data)

    def test_encrypt(self):
        netpack_mgr = NetPacketMgr()
        for i in range(100):
            data = self.get_rand_str()
            packet_body = netpack_mgr._encrypt(data)
            new_data = netpack_mgr._decrypt(packet_body)
            self.assertEqual(data, new_data)


if __name__ == "__main__":
    unittest.main()
