# TODO: Implement Schema
# TODO: Implement send()
# TODO: Implement receive()

from datetime import datetime, timezone
import socket
import config

from states.client_state import client_state
from custom_types.base_message import BaseMessage
from custom_types.fields import UserID, Token, Timestamp, TTL
from datetime import datetime, timezone
from utils import msg_format
from client_logger import client_logger

class GroupUpdate(BaseMessage):
    TYPE = "GROUP_UPDATE"
    __hidden__ = False
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "GROUP_ID": {"type": str, "required": True},
        "ADD": {"type": str, "required": True},
        "REMOVE": {"type": str, "required": False},
        "TIMESTAMP": {"type": Timestamp, "required": True},
        "TOKEN": {"type": Token, "required": True},
    }

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "GROUP_ID": self.group_id,
            "ADD": self.add,
            "REMOVE": self.remove,
            "TIMESTAMP": self.timestamp,
            "TOKEN": self.token,
        }
    
    def __init__(self, group_id: str, add: str, remove: str = "", ttl: TTL = 3600):
        unix_now = int(datetime.now(timezone.utc).timestamp())
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.group_id = group_id
        self.add = add
        self.remove = remove
        self.timestamp = Timestamp(unix_now)
        self.token = Token(self.from_user, self.timestamp + ttl, Token.Scope.GROUP)

    @classmethod
    def parse(cls, data: dict) -> "GroupUpdate":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.group_id = data["GROUP_ID"]
        new_obj.add = data["ADD"]
        new_obj.remove = data.get("REMOVE")
        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        new_obj.token = Token.parse(data["TOKEN"])
        Token.validate_token(new_obj.token, expected_scope=Token.Scope.GROUP, expected_user_id=new_obj.from_user)

        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj


    def send(self, sock: socket.socket, ip: str = "default", port: int = 50999, encoding: str = "utf-8"):
        msg = msg_format.serialize_message(self.payload)

        # --- Add new members ---
        if hasattr(self, "add") and self.add:
            group_members = msg_format.string_to_list(self.add)
            for add_user in group_members:
                try:
                    client_state.add_group_member(self.group_id, UserID.parse(add_user))
                except ValueError as e:
                    client_logger.error(f"Error adding member {add_user} to group {self.group_id}: {str(e)}")

        # --- Remove members ---
        if hasattr(self, "remove") and self.remove:
            remove_members = msg_format.string_to_list(self.remove)
            for rem_user in remove_members:
                try:
                    client_state.remove_group_member(self.group_id, UserID.parse(rem_user))
                except ValueError as e:
                    client_logger.error(f"Error removing member {rem_user} from group {self.group_id}: {str(e)}")

        # --- Send to all peers ---
        for peer in client_state.get_peers():
            try:
                peer_ip = str(peer).split('@')[1]
                sock.sendto(msg.encode(encoding), (peer_ip, port))
                client_logger.debug(f"Sent group update message to peer {peer} at {peer_ip}:{port}")
            except Exception as e:
                client_logger.error(f"Error sending to {peer} ({str(e)})")

        return (ip, port)


    @classmethod
    def receive(cls, raw: str) -> "GroupUpdate":
        received = cls.parse(msg_format.deserialize_message(raw))

        # --- Add members ---
        if hasattr(received, "add") and received.add:
            group_members = msg_format.string_to_list(received.add)
            for member in group_members:
                try:
                    client_state.add_group_member(received.group_id, UserID.parse(member))
                except ValueError as e:
                    client_logger.error(f"Error adding member {member} to group {received.group_id}: {str(e)}")

        # --- Remove members ---
        if hasattr(received, "remove") and received.remove:
            remove_members = msg_format.string_to_list(received.remove)
            for member in remove_members:
                try:
                    client_state.remove_group_member(received.group_id, UserID.parse(member))
                    if member == client_state.get_user_id():
                        client_state.remove_group(received.group_id)
                except ValueError as e:
                    client_logger.error(f"Error removing member {member} from group {received.group_id}: {str(e)}")
        return received



    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        display_name = client_state.get_peer_display_name(self.from_user)
        if display_name != "":
            return f"{display_name} sent \"{self.content}\""
        return f"{self.from_user} sent \"{self.content}\""



__message__ = GroupUpdate
