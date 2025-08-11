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
        """
        Send to all peers, but DROP if group_id is not unique locally.
        """
        # 1) Enforce uniqueness locally
        if self.group_id in client_state.get_group_ids():
            client_logger.warning(f"Dropping GROUP_CREATE for '{self.group_id}': duplicate group_id")
            return (ip, port)

        # 2) Broadcast to all peers
        msg = msg_format.serialize_message(self.payload)
        last_ip = "0.0.0.0"
        for peer in client_state.get_peers():
            try:
                # Peer may be a UserID or a 'name@ip' string
                if hasattr(peer, "get_ip"):
                    peer_ip = peer.get_ip()
                else:
                    peer_str = str(peer)
                    peer_ip = peer_str.split("@", 1)[1] if "@" in peer_str else peer_str

                socket.sendto(msg.encode(encoding), (peer_ip, port))
                client_logger.debug(f"Sent GROUP_CREATE to peer {peer} at {peer_ip}:{port}")
                last_ip = peer_ip
            except Exception as e:
                client_logger.error(f"Error sending GROUP_CREATE to {peer}: {e}")

        return (last_ip, port)


    @classmethod
    def receive(cls, raw: str) -> "GroupCreate":
        """
        If the receiver is in MEMBERS → create and store full group in _groups.
        If not → only store group_id in _group_ids.
        DROP if group_id already known (idempotent / uniqueness).
        """
        received = cls.parse(msg_format.deserialize_message(raw))

        # 1) Drop duplicates (already known group_id)
        if received.group_id in client_state.get_group_ids():
            client_logger.debug(f"Ignoring GROUP_CREATE '{received.group_id}': group_id already known")
            return received

        # 2) Decide based on membership
        group_members = msg_format.string_to_list(received.members)
        member_ids = [UserID.parse(member) for member in group_members]
        me = client_state.get_user_id()

        if me in member_ids:
            # Receiver is part of the group → create full group entry
            client_state.create_group(received.group_id, received.group_name, member_ids)
            client_logger.debug(
                f"Created group locally from GROUP_CREATE: {received.group_id} ({received.group_name}) with members: {member_ids}"
            )
        else:
            # Not a member → only track the ID
            client_state.add_group_id(received.group_id)
            client_logger.debug(f"Stored group_id only (not a member): {received.group_id}")

        return received

__message__ = GroupCreate