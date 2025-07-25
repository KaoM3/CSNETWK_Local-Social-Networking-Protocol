# TODO: Implement Schema
# TODO: Implement send()
# TODO: Implement receive()

from custom_types.user_id import UserID
from custom_types.token import Token
from datetime import datetime, timezone
from utils import msg_format
from custom_types.base_message import BaseMessage

class Post(BaseMessage):
    """
    Represents a POST message containing user-generated content.
    """

    TYPE = "POST"

    __schema__ = {
        "TYPE": TYPE,
        "USER_ID": {"type": UserID, "required": True, "input": True},
        "CONTENT": {"type": str, "required": True, "input": True},
        "TTL": {"type": int, "required": True},
        "MESSAGE_ID": {"type": str, "required": True},
        "TOKEN": {"type": str, "required": True},
    }

    @property
    def payload(self) -> dict:
        return {
            "TYPE": self.TYPE,
            "USER_ID": self.user_id,
            "CONTENT": self.content,
            "TTL": self.ttl,
            "MESSAGE_ID": self.message_id,
            "TOKEN": self.token,
        }

    def __init__(self, user_id: UserID, content: str, ttl: int = 3600):
        unix_now = int(datetime.now(timezone.utc).timestamp())
        self.type = self.TYPE
        self.user_id = user_id
        self.content = content
        self.ttl = ttl
        self.message_id = msg_format.generate_message_id()
        self.token = Token(user_id, unix_now + ttl, Token.Scope.BROADCAST)

    @classmethod
    def parse(cls, data: dict) -> "Post":
        return cls.__new__(cls)._init_from_dict(data)

    def _init_from_dict(self, data: dict):
        self.type = data["TYPE"]
        self.user_id = UserID.parse(data["USER_ID"])
        self.content = str(data["CONTENT"])
        self.ttl = int(data["TTL"])

        message_id = data["MESSAGE_ID"]
        msg_format.validate_message_id(message_id)
        self.message_id = message_id

        self.token = Token.parse(data["TOKEN"])
        msg_format.validate_message(self.payload, self.__schema__)
        return self

    @classmethod
    def receive(cls, raw: str) -> "Post":
        return cls.parse(msg_format.deserialize_message(raw))


__message__ = Post
  