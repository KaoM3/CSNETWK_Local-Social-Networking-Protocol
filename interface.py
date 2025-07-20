import router
import config
import keyword
from states import client
from custom_types.user_id import UserID
import custom_types.token as token
from messages.base_message import BaseMessage
type_parsers = {
    UserID: UserID.parse,
    token.Token: token.Token.parse,
    # add more types as needed
}

def print_message(msg_obj: BaseMessage):
  """
  Prints the message's payload in a readable format.
  """
  for field, value in msg_obj.payload.items():
    print(f"{field}: {value}")

def create_profile_message():
  profile_class = router.get_module("PROFILE")  # This returns the Profile class
  schema = profile_class.__schema__
  fields = {}

  for key, value in schema.items():
    if key == "TYPE":
      continue
    if value.get("input", False):
      user_input = input(f"Enter {key}: ").strip()
      while not user_input:
        user_input = input(f"{key} cannot be empty. Try again: ").strip()
      fields[key] = user_input

      if key == "DISPLAY_NAME":
        # Generate the USER_ID from display name + broadcast IP
        user_id = client.get_user_id()
        fields["USER_ID"] = user_id

  profile_obj = profile_class(
    user_id=fields["USER_ID"],
    display_name=fields["DISPLAY_NAME"],
    status=fields["STATUS"]
  )
  print_message(profile_obj)
  return profile_obj

def create_message(msg_type: str):
  """
  Creates a new message object of msg_type.

  Parameters:
    msg_type (str): The identifier for the message class to create.

  Returns:
    An instance of the message class initialized with user-provided values.

  """
  msg_class = router.get_module(msg_type)
  msg_schema = msg_class.__schema__

  new_msg_args = {}
  for key, value in msg_schema.items():
    if key == "TYPE":
      continue
    if value.get("input", False):
      while True:
        user_input = input(f"Enter {key}: ").strip()
        while not user_input:
          user_input = input(f"{key} cannot be empty. Try again: ").strip()
        typ = value.get("type", None)
        parser = type_parsers.get(typ)
        arg_name = key.lower()
        if keyword.iskeyword(arg_name):
          arg_name = arg_name+"_"
        if parser:
          try:
            new_msg_args[arg_name] = parser(user_input)
            break
          except Exception as e:
            print(f"{e}")
        else:
          new_msg_args[arg_name] = user_input  # fallback or raise error
          break

  print(new_msg_args)
  new_msg_obj = msg_class(**new_msg_args)
  print_message(new_msg_obj)
  return new_msg_obj

def get_user_id() -> str:
  username = input("Enter username: ")
  user_id = f"{username}@{config.CLIENT_IP}"
  print(f"WELCOME \"{user_id}\"!")
  return user_id