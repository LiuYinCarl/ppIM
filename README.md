# ppIM

## process

the begin part of the communication between client and server 

```
        set_name_req
client -----------------------> server

        set_name_res
client <----------------------- server

        room_list_notify
client <----------------------- server

        select_room_req
client -----------------------> server

        select_room_res
client <----------------------- server

        room_members_list_notify
client <----------------------- server

              new_node_join_notify
other client <----------------------- server

```