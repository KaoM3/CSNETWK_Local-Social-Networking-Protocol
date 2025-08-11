from datetime import datetime, timezone
import socket

from custom_types.fields import UserID, Token, Timestamp, TTL
from custom_types.base_message import BaseMessage
from utils import msg_format
from states.client_state import client_state
from client_logger import client_logger


class GroupUpdate(BaseMessage):
    TYPE = "GROUP_UPDATE"
    SCOPE = Token.Scope.GROUP
    __hidden__ = False
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "GROUP_ID": {"type": str, "required": True},
        "ADD": {"type": str, "required": False},
        "REMOVE": {"type": str, "required": False},
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
        # Only include when non-empty; schema allows omission
        if self.add:
            p["ADD"] = self.add
        if self.remove:
            p["REMOVE"] = self.remove
        return p

    def __init__(self, group_id: str, add: str = "", remove: str = "", ttl: TTL = 3600):
        unix_now = int(datetime.now(timezone.utc).timestamp())
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.group_id = str(group_id)
        self.add = (add or "").strip()       # comma-separated UserIDs in wire format
        self.remove = (remove or "").strip() # comma-separated UserIDs in wire format
        self.timestamp = Timestamp(unix_now)
        self.token = Token(self.from_user, self.timestamp + ttl, self.SCOPE)

    @classmethod
    def parse(cls, data: dict) -> "GroupUpdate":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.group_id = data["GROUP_ID"]
        new_obj.add = data.get("ADD", "") or ""
        new_obj.remove = data.get("REMOVE", "") or ""
        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        new_obj.token = Token.parse(data["TOKEN"])
        Token.validate_token(new_obj.token, expected_scope=cls.SCOPE, expected_user_id=new_obj.from_user)
        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    def send(self, socket: socket.socket, ip: str = "default", port: int = 50999, encoding: str = "utf-8") -> tuple[str, int]:
        """
        Broadcast to all:
          recipients = (current members ∪ added) − removed − self
        Returns (last_ip, port) for compatibility with callers that index the result.
        """
        group = client_state.get_group(self.group_id)
        if not group:
            client_logger.error(f"Cannot send GROUP_UPDATE: Group '{self.group_id}' does not exist")
            return (ip, port)

        # Start from current members
        recipients = set(client_state.get_group_members(self.group_id))

        # + ADDed members (so they also receive the update that includes them)
        if self.add:
            recipients |= {UserID.parse(u) for u in msg_format.string_to_list(self.add)}

        # - REMOVEd members (don't send to those we’re removing)
        #if self.remove:
            #recipients -= {UserID.parse(u) for u in msg_format.string_to_list(self.remove)}

        # - self
        #if self.from_user in recipients:
            #recipients.remove(self.from_user)

        # Serialize once
        msg = msg_format.serialize_message(self.payload)

        last_ip = "0.0.0.0"
        sent = 0
        for uid in recipients:
            try:
                # Ensure UserID instance
                if not isinstance(uid, UserID):
                    uid = UserID.parse(str(uid))
                dst_ip = uid.get_ip()
                socket.sendto(msg.encode(encoding), (dst_ip, port))
                client_logger.debug(f"Sent GROUP_UPDATE to {uid} at {dst_ip}:{port}")
                last_ip = dst_ip
                sent += 1
            except Exception as e:
                client_logger.error(f"Failed sending GROUP_UPDATE to {uid}: {e}")

        if sent == 0:
            client_logger.warning(f"No recipients for GROUP_UPDATE {self.group_id} (nothing sent).")
            return (ip if ip != "default" else "default", port)
        return (last_ip, port)

    @classmethod
    def receive(cls, raw: str) -> "GroupUpdate":
        """
        Apply ADD/REMOVE using a consolidated client_state helper.
        """
        received = cls.parse(msg_format.deserialize_message(raw))

        add_members = [UserID.parse(u) for u in msg_format.string_to_list(received.add)] if received.add else []
        remove_members = [UserID.parse(u) for u in msg_format.string_to_list(received.remove)] if received.remove else []

        # This single helper updates self._groups[group_id]['members']
        client_state.upsert_group_members(
            group_id=received.group_id,
            group_name=None,                 # name unchanged on updates
            add_members=add_members,
            remove_members=remove_members
        )
        
        # If *this* client was removed, drop the entire group locally
        me = client_state.get_user_id()
        if any(u == me for u in remove_members):
            try:
                client_state.remove_group(received.group_id)
            except Exception:
                pass

        return received

    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        who = client_state.get_peer_display_name(self.from_user) or str(self.from_user)
        parts = []
        if self.add: parts.append(f"added {self.add}")
        if self.remove: parts.append(f"removed {self.remove}")
        changes = ", ".join(parts) if parts else "no changes"
        return f"{who} updated group {self.group_id}: {changes}"


__message__ = GroupUpdate
