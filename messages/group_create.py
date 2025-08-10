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



class GroupCreate(BaseMessage):
    TYPE = "GROUP_CREATE"
    SCOPE = Token.Scope.GROUP
    __hidden__ = False
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "GROUP_ID": {"type": str, "required": True},
        "GROUP_NAME": {"type": str, "required": True},
        "MEMBERS": {"type": str, "required": True},  # raw string in wire format
        "TIMESTAMP": {"type": Timestamp, "required": True},
        "TOKEN": {"type": Token, "required": True},
    }

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "GROUP_ID": self.group_id,
            "GROUP_NAME": self.group_name,
            "MEMBERS": self.members,
            "TIMESTAMP": self.timestamp,
            "TOKEN": self.token,
        }

    def __init__(self, group_id: str, group_name: str, members: str, ttl: TTL = 3600):
        """
        members: comma-separated string of user IDs
        """
        unix_now = int(datetime.now(timezone.utc).timestamp())
        group_members = msg_format.string_to_list(members)  # Convert to list of UserID objects
        # Convert members to UserID objects
        member_ids = [UserID.parse(member) for member in group_members]
        # Add current user to the group members if not already included
        current_user = client_state.get_user_id()
        if current_user not in member_ids:
            member_ids.append(current_user)
        # Create the group in client state
        client_state.create_group(group_id, group_name, member_ids)
        
        self.type = self.TYPE
        self.from_user = current_user
        self.group_id = group_id
        self.group_name = group_name
        # Convert comma-separated string into a list of UserID objects
        self.members = members
        self.timestamp = Timestamp(unix_now)
        self.ttl = ttl
        self.token = Token(self.from_user, self.timestamp + self.ttl, self.SCOPE)

    @classmethod
    def parse(cls, data: dict) -> "GroupCreate":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.group_id = data["GROUP_ID"]
        new_obj.group_name = data["GROUP_NAME"]
        # Parse raw string to list
        new_obj.members = data["MEMBERS"]
        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        new_obj.token = Token.parse(data["TOKEN"])
        Token.validate_token(new_obj.token, expected_scope=cls.SCOPE, expected_user_id=new_obj.from_user)
        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    def send(self, socket: socket.socket, ip: str = "default", port: int = 50999, encoding: str = "utf-8"):
        msg = msg_format.serialize_message(self.payload)
        # Group create messages should be sent to all peers
        for peer in client_state.get_peers():
            #if peer != self.from_user:  # Don't send to self
                try:
                    socket.sendto(msg.encode(encoding), (str(peer), port))
                    client_logger.debug(f"Sent group create message to peer {peer}:{port}")
                except Exception as e:
                    client_logger.error(f"Error sending to {peer}: {e}")
        return (ip, port)


    @classmethod
    def receive(cls, raw: str) -> "GroupCreate":
        received = cls.parse(msg_format.deserialize_message(raw))
        # When receiving a group create message, add the group to client state
        group_members = msg_format.string_to_list(received.members)
        member_ids = [UserID.parse(member) for member in group_members]
        # Add current user to the group members if included in the message
        current_user = client_state.get_user_id()
        if current_user in member_ids:
            client_state.create_group(received.group_id, received.group_name, member_ids)
        return received

    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        display_name = client_state.get_peer_display_name(self.from_user)
        member_count = len(msg_format.string_to_list(self.members))
        if display_name != "":
            return f"{display_name} created group '{self.group_name}' with {member_count} members"
        return f"{self.from_user} created group '{self.group_name}' with {member_count} members"


__message__ = GroupCreate
