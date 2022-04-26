# 一个网络包的格式
# 前 2 字节表示这个包的长度 n, 接下来的 2 字节表示这个包的内容

import logging
import unittest

MAX_PACK_SIZE = (1 << 17) - 1

class NetPacketMgr(object):
    def __init__(self):
        self.msg = []
        self.msgpond = b""
        self.msg_len = 0

    def get_packet_head_len(self, packet_head):
        return int.from_bytes(packet_head, byteorder="big")

    def make_packet_head(self, packet_body_len):
        if packet_body_len > MAX_PACK_SIZE:
            return False, None

        head = packet_body_len.to_bytes(4, byteorder="big")
        return True, head

    def pack_msg(self, data):
        bdata = data.encode(encoding="utf8")
        str_len = str(len(bdata))
        return self


class TestNetPacketMgr(unittest.TestCase):
    def test_pack_head(self):
        netpack_mgr = NetPacketMgr()
        for packet_len in range(1, MAX_PACK_SIZE):
            ok, head = netpack_mgr.make_packet_head(packet_len)
            if ok == False:
                logging.error("pack head failed.")
                return
            new_packet_len = netpack_mgr.get_packet_head_len(head)
            assert packet_len == new_packet_len, "packet_len:{} new_packet_len:{}".format(packet_len, new_n)


if __name__ == "__main__":
    unittest.main()