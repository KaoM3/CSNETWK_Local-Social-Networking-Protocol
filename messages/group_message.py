from datetime import datetime, timezone
import socket
from custom_types.fields import UserID, Token, Timestamp, MessageID, TTL
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from utils import msg_format
from client_logger import client_logger

class GroupMessage(BaseMessage):
    TYPE = "GROUP_MESSAGE"
    __hidden__ = False
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "GROUP_ID": {"type": str, "required": True},
        "CONTENT": {"type": str, "required": True},
        "MESSAGE_ID": {"type": MessageID, "required": True},
        "TIMESTAMP": {"type": Timestamp, "required": True},
        "TOKEN": {"type": Token, "required": True},
    }

    def __init__(self, group_id: str, content: str, ttl: TTL = 3600):
        """
        Initialize a new group message
        Args:
            group_id: The ID of the group to send the message to
            content: The text message to send
            ttl: Time-to-live for the message token
        """
        # Verify the group exists and user is a member
        group = client_state.get_group(group_id)
        if not group:
            raise ValueError(f"Group '{group_id}' does not exist")
        
        current_user = client_state.get_user_id()
        if not client_state.is_group_member(group_id, current_user):
            raise ValueError(f"You are not a member of group '{group_id}'")

        unix_now = int(datetime.now(timezone.utc).timestamp())
        self.type = self.TYPE
        self.from_user = current_user
        self.group_id = group_id
        self.content = content
        self.timestamp = Timestamp(unix_now)
        self.message_id = MessageID.generate()
        self.token = Token(self.from_user, self.timestamp + ttl, Token.Scope.GROUP)

    @classmethod
    def parse(cls, data: dict) -> "GroupMessage":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.group_id = data["GROUP_ID"]
        new_obj.content = data["CONTENT"]
        new_obj.message_id = MessageID.parse(data["MESSAGE_ID"])
        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        new_obj.token = Token.parse(data["TOKEN"])
        Token.validate_token(new_obj.token, expected_scope=Token.Scope.GROUP, expected_user_id=new_obj.from_user)

        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "GROUP_ID": self.group_id,
            "CONTENT": self.content,
            "MESSAGE_ID": self.message_id,
            "TIMESTAMP": self.timestamp,
            "TOKEN": self.token,
        }

    def send(self, socket: socket.socket, ip: str = "default", port: int = 50999, encoding: str = "utf-8"):
        """Send the group message to all members of the group"""
        # Get the group members
        group = client_state.get_group(self.group_id)
        if not group:
            client_logger.error(f"Cannot send message: Group '{self.group_id}' does not exist")
            return (ip, port)

        msg = msg_format.serialize_message(self.payload)
        # Send to all group members except self
        for member in group["members"]:
            if member != self.from_user:
                try:
                    # Extract IP address from UserID (format is username@ip)
                    member_ip = str(member).split('@')[1]
                    socket.sendto(msg.encode(encoding), (member_ip, port))
                    client_logger.debug(f"Sent group message to member {member} at {member_ip}:{port}")
                except Exception as e:
                    client_logger.error(f"Error sending to {member}: {str(e)}")

        # Add to client state's recent messages
        client_state.add_recent_message_sent(self)
        return (ip, port)

    @classmethod
    def receive(cls, raw: str) -> "GroupMessage":
        """Receive and process an incoming group message"""
        received = cls.parse(msg_format.deserialize_message(raw))
        
        # Verify the group exists and receiving user is a member
        current_user = client_state.get_user_id()
        if client_state.is_group_member(received.group_id, current_user):
            client_state.add_recent_message_received(received)
            client_logger.debug(f"Received group message in group {received.group_id} from {received.from_user}")
        else:
            client_logger.debug(f"Dropped message: Not a member of group {received.group_id}")
        
        return received

    def info(self, verbose: bool = False) -> str:
        """Format the message for display"""
        if verbose:
            return f"{self.payload}"
        display_name = client_state.get_peer_display_name(self.from_user)
        if display_name != "":
            return f"{display_name} sent \"{self.content}\""
        return f"{self.from_user} sent \"{self.content}\""


__message__ = GroupMessage
