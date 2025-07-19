import router
import config
import utils.msg_format as msg_format
from messages.base_message import BaseMessage
from custom_types.user_id import UserID
import custom_types.token as token

if __name__ == "__main__":
  router.load_messages(config.MESSAGES_DIR)

  classes = []
  classes.append(router.get_module("DM"))
  classes.append(router.get_module("PING"))
  classes.append(router.get_module("PROFILE"))

  from_user = UserID("alice", "192.168.1.11")
  to_user = UserID("bob", "192.168.1.12")
  user_token = token.Token(from_user, 1728942100, token.Scope.CHAT)

  msg = {
    "TYPE": "DM",
    "FROM": from_user,
    "TO": to_user,
    "CONTENT": "Hello Bob!",
    "TIMESTAMP": 1728938500,
    "MESSAGE_ID": "f83d2b1df83d2b1d",
    "TOKEN": user_token
  }

  serialized_msg = msg_format.serialize_message(msg)
  deserialized_msg = msg_format.deserialize_message(serialized_msg)

  for obj in classes:
    try:
      msg_obj = obj.parse(deserialized_msg)
      print(str(msg_obj))
      if isinstance(msg_obj, BaseMessage):
        msg_obj.send()
      #obj.receive(serialized_msg)
    except Exception as e:
      print("\nERROR: ")
      print(e)