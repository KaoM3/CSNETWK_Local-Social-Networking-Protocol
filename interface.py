import router
import config
from states import client
from messages.base_message import BaseMessage

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


def get_user_id() -> str:
  username = input("Enter username: ")
  user_id = f"{username}@{config.CLIENT_IP}"
  print(f"WELCOME \"{user_id}\"!")
  return user_id