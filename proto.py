from collections import namedtuple


############### error code define #####################

ECODE_DEF = namedtuple("ECODE_DEF", 
    """ success
        illegal_nick_name
        room_not_exist
    """)

ECODE = ECODE_DEF(
    success         = 1,
    illegal_nick_name = 2,
    room_not_exist  = 3,
)

PROTO_DEF = namedtuple("PROTO_DEF",
        """ S_ROOM_LIST_NOTIFY
            C_SELECT_ROOM_REQ
            S_SELECT_ROOM_RES
            C_SET_NAME_REQ
            S_SET_NAME_RES
        """)
PROTO = PROTO_DEF(
    S_ROOM_LIST_NOTIFY  = 1,
    C_SELECT_ROOM_REQ   = 2,
    S_SELECT_ROOM_RES   = 3,
    C_SET_NAME_REQ      = 4,
    S_SET_NAME_RES      = 5,
)


########### proto define #####################

# # server send room list to client
# S_ROOM_LIST_NOTIFY = namedtuple("S_SEND_ROOM_LIST", "room_info")

# # client select a room to enter
# C_SELECT_ROOM_REQ = namedtuple("C_SELECT_ROOM_REQ", "room_id")

# # server tell client the result of select room
# S_SELECT_ROOM_RES = namedtuple("S_SELECT_ROOM_RES", "room_id", "ecode")

# # client tell server want to set user name
# C_SET_NAME_REQ = namedtuple("C_SET_NAME_REQ", "name")

# # server tell client the result of set user name
# S_SET_NAME_RES = namedtuple("S_SET_NAME_RES", "ecode")
