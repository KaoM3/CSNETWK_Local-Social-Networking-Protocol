import router
import config
from custom_types.user_id import UserID


def print_profile_message(profile_obj):
  """
  Prints the profile message in a readable format.
  """
  print(f"Profile Message:")
  print(f"  USER_ID: {profile_obj.user_id}")
  print(f"  DISPLAY_NAME: {profile_obj.display_name}")
  print(f"  STATUS: {profile_obj.status}")
  print(f"  TYPE: {profile_obj.TYPE}")


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
        display_name = user_input
        user_id = f"{display_name}@{config.CLIENT_IP}"
        fields["USER_ID"] = user_id

  profile_obj = profile_class(
    user_id=fields["USER_ID"],
    display_name=fields["DISPLAY_NAME"],
    status=fields["STATUS"]
  )
  print_profile_message(profile_obj)
  return profile_obj


def get_user_id() -> str:
  username = input("Enter username: ")
  user_id = f"{username}@{config.CLIENT_IP}"
  print(f"WELCOME \"{user_id}\"!")
  return user_id