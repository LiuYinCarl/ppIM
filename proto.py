from collections import namedtuple


############### error code define #####################

ECODE_DEF = namedtuple("ECODE_DEF", 
    """ success
        illegal_nick_name
        room_not_exist
        join_room_failed
    """)

ECODE = ECODE_DEF(
    success         = 1,
    illegal_nick_name = 2,
    room_not_exist  = 3,
    join_room_failed = 4,
)

PROTO_DEF = namedtuple("PROTO_DEF",
        """ S_ROOM_LIST_NOTIFY
            C_SELECT_ROOM_REQ
            S_SELECT_ROOM_RES
            C_SET_NAME_REQ
            S_SET_NAME_RES
            C_SEND_MSG_REQ
            S_MSG_NOTIFY
        """)
PROTO = PROTO_DEF(
    S_ROOM_LIST_NOTIFY  = 1,
    C_SELECT_ROOM_REQ   = 2,
    S_SELECT_ROOM_RES   = 3,
    C_SET_NAME_REQ      = 4,
    S_SET_NAME_RES      = 5,
    C_SEND_MSG_REQ      = 6,
    S_MSG_NOTIFY        = 7,
)
