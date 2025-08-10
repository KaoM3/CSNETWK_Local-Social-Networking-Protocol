# TODO: Implement Schema
# TODO: Implement send()
# TODO: Implement receive()

from datetime import datetime, timezone
from custom_types.fields import UserID, Token, Timestamp, MessageID, TTL
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from utils import msg_format

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
        unix_now = int(datetime.now(timezone.utc).timestamp())
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
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

__message__ = GroupMessage
