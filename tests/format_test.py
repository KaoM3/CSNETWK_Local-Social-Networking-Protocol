import utils.msg_format as msg_format
from custom_types.user_id import UserID
from custom_types.token import Token

if __name__ == "__main__":
  from_user = UserID("alice", "192.168.1.11")
  to_user = UserID("bob", "192.168.1.12")
  user_token = Token("alice", 1728942100, Token.Scope.CHAT)

  msg = {
    "TYPE": "DM",
    "FROM": from_user,
    "TO": to_user,
    "CONTENT": "Hello Bob!",
    "TIMESTAMP": 1728938500,
    "MESSAGE_ID": "f83d2b1d",
    "TOKEN": user_token
  }

  print(msg)

  print("Serialized Message\n")
  msg = msg_format.serialize_message(msg)
  print(msg)
  print("Deserialized Message\n")
  msg = msg_format.deserialize_message(msg)
  print(msg)
