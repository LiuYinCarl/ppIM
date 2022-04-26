# 一个网络包的格式
# 前 2 字节表示这个包的长度 n, 接下来的 2 字节表示这个包的内容

import logging
import unittest
import random
from Crypto.Cipher import AES
import base64

PACKET_HEAD_LENGTH = 2
MAX_PACK_SIZE = (1 << 16) - 1
AES_SECRET_KEY = b"ufahdufhaiufugil"

class NetPacketMgr(object):
    def __init__(self, socket=None):
        self.aes = AES.new(AES_SECRET_KEY, AES.MODE_ECB)
        self.socket = socket
        self.send_packet_list = []
        self.recv_packet_list = []
        self.recv_cache = bytes()

    def pack_header(self, packet_body_len) -> bytes:
        if packet_body_len > MAX_PACK_SIZE:
            return False, None
        head = packet_body_len.to_bytes(PACKET_HEAD_LENGTH, byteorder="big")
        return True, head
    
    def unpack_header(self, packet_header) -> int:
        return int.from_bytes(packet_header, byteorder="big")

    def pack_body(self, data:str) -> bytes:
        return bytes(data, encoding="utf8")

    def unpack_body(self, packet_body:bytes) -> str:
        return str(packet_body, encoding="utf8")

    def encrypt(self, data:str) -> str:
        data = data.encode("utf8")
        while len(data) % 16 != 0:
            data += b"\x00"
        en_data = self.aes.encrypt(data)
        return str(base64.b64encode(en_data), encoding="utf8")

    def decrypt(self, data:str) -> str:
        data = data.encode("utf8")
        data = base64.b64decode(data)
        de_data = self.aes.decrypt(data)
        return str(de_data, encoding="utf8").strip('\0')
    
    def pack(self, data:str):
        body = self.pack_body(data)
        header = self.pack_header(len(body))
        packet = header + body
        return packet

    def send(self, data:str) -> bool:
        packet = self.pack(data)
        self.send_packet_list.append(packet)
        while len(self.send_packet_list) > 0:
            # TODO check if socket send is success
            self.socket.send(self.send_packet_list[0])
            self.send_packet_list.pop[0]

    def recv(self) -> str:
        data = self.socket.recv(1024)
        self.recv_cache += data
        if len(self.recv_cache) < PACKET_HEAD_LENGTH:
            return None # still not receive a full packet header
        header = self.recv_cache[:PACKET_HEAD_LENGTH]
        body_len = self.unpack_header(header)
        if PACKET_HEAD_LENGTH + body_len > len(self.recv_cache):
            return None # still not receive a full packet
        packet_size = PACKET_HEAD_LENGTH + body_len
        body = self.recv_cache[PACKET_HEAD_LENGTH: packet_size]
        self.recv_cache = self.recv_cache[:packet_size] # remove first packet
        data = self.unpack_body(body)
        return data




class TestNetPacketMgr(unittest.TestCase):
    def get_rand_str(self):
        s = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        res = [random.choice(s) for i in range(100)]
        return "".join(res)

    def test_pack_header(self):
        netpack_mgr = NetPacketMgr()
        for packet_len in range(1, MAX_PACK_SIZE):
            ok, head = netpack_mgr.pack_header(packet_len)
            self.assertTrue(ok)
            new_packet_len = netpack_mgr.unpack_header(head)
            self.assertEqual(packet_len, new_packet_len)
    
    def test_pack_body(self):
        netpack_mgr = NetPacketMgr()
        for i in range(100):
            data = self.get_rand_str()
            packet_body = netpack_mgr.pack_body(data)
            new_data = netpack_mgr.unpack_body(packet_body)
            self.assertEqual(data, new_data)

    def test_encrypt(self):
        netpack_mgr = NetPacketMgr()
        for i in range(100):
            data = self.get_rand_str()
            packet_body = netpack_mgr.encrypt(data)
            new_data = netpack_mgr.decrypt(packet_body)
            self.assertEqual(data, new_data)


if __name__ == "__main__":
    unittest.main()