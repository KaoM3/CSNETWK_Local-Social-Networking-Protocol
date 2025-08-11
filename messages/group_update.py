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
        "ADD": {"type": str, "required": False},      # <-- optional
        "REMOVE": {"type": str, "required": False},   # <-- optional
        "TIMESTAMP": {"type": Timestamp, "required": True},
        "TOKEN": {"type": Token, "required": True},
    }

    @property
    def payload(self) -> dict:
        p = {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "GROUP_ID": self.group_id,
            "TIMESTAMP": self.timestamp,
            "TOKEN": self.token,
        }
        if getattr(self, "add", None):
            p["ADD"] = self.add
        if getattr(self, "remove", None):
            p["REMOVE"] = self.remove
        return p

    def __init__(self, group_id: str, add: str = "", remove: str = "", ttl: TTL = 3600):
        unix_now = int(datetime.now(timezone.utc).timestamp())
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.group_id = group_id
        self.add = add.strip()
        self.remove = remove.strip()
        self.timestamp = Timestamp(unix_now)
        self.token = Token(self.from_user, self.timestamp + ttl, Token.Scope.GROUP)
    
    @classmethod
    def parse(cls, data: dict) -> "GroupUpdate":  # match parent signature
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.group_id = data["GROUP_ID"]
        new_obj.add = data.get("ADD", "")
        new_obj.remove = data.get("REMOVE", "")
        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        new_obj.token = Token.parse(data["TOKEN"])
        Token.validate_token(
            new_obj.token,
            expected_scope=Token.Scope.GROUP,
            expected_user_id=new_obj.from_user
        )
        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    def send(self, sock: socket.socket, ip: str = "default", port: int = 50999, encoding: str = "utf-8"):
        # Update local state first
        if self.add:
            for u in msg_format.string_to_list(self.add):
                try:
                    client_state.add_group_member(self.group_id, UserID.parse(u))
                except ValueError as e:
                    client_logger.error(f"Error adding {u} to {self.group_id}: {e}")

        if self.remove:
            for u in msg_format.string_to_list(self.remove):
                try:
                    client_state.remove_group_member(self.group_id, UserID.parse(u))
                except ValueError as e:
                    client_logger.error(f"Error removing {u} from {self.group_id}: {e}")

        # Compute recipients: (current members ∪ added) − removed − self
        recipients = set(client_state.get_group_members())
        if self.add:
            recipients |= {UserID.parse(u) for u in msg_format.string_to_list(self.add)}
        if self.remove:
            recipients -= {UserID.parse(u) for u in msg_format.string_to_list(self.remove)}
        if self.from_user in recipients:
            recipients.remove(self.from_user)

        # Send to each recipient directly (even if not in peers)
        sent = 0
        for uid in recipients:
            try:
                dst_ip = uid.get_ip()
                super().send(sock, dst_ip, port, encoding)  # uses same serialization consistently
                client_logger.debug(f"Sent GROUP_UPDATE to {uid} at {dst_ip}:{port}")
                sent += 1
            except Exception as e:
                client_logger.error(f"Failed sending GROUP_UPDATE to {uid}: {e}")

        if sent == 0:
            client_logger.warning(f"No recipients for GROUP_UPDATE {self.group_id} (nothing sent).")
        return sent

    @classmethod
    def receive(cls, raw: str) -> "GroupUpdate":
        received = cls.parse(msg_format.deserialize_message(raw))

        # Apply adds
        if received.add:
            for member in msg_format.string_to_list(received.add):
                try:
                    client_state.add_group_member(received.group_id, UserID.parse(member))
                except ValueError as e:
                    client_logger.error(f"Add fail {member} -> {received.group_id}: {e}")

        # Apply removes
        removed_self = False
        if received.remove:
            current_user = client_state.get_user_id()
            for m_str in msg_format.string_to_list(received.remove):
                try:
                    uid = UserID.parse(m_str)
                    client_state.remove_group_member(received.group_id, uid)
                    if uid == current_user:
                        removed_self = True
                except ValueError as e:
                    client_logger.error(f"Remove fail {m_str} -> {received.group_id}: {e}")

        # Drop group locally if we were removed or the group is empty
        if removed_self:
            client_state.remove_group(received.group_id)
        else:
            grp = client_state.get_group(received.group_id)
            if grp is not None and not grp.get("members"):
                client_state.remove_group(received.group_id)

        return received





    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        display_name = client_state.get_peer_display_name(self.from_user)
        if display_name != "":
            return f"{display_name} sent \"{self.content}\""
        return f"{self.from_user} sent \"{self.content}\""



__message__ = GroupUpdate
