import router
import config
import keyword
import log
from states import client
from custom_types.user_id import UserID
from custom_types.token import Token
from custom_types.base_message import BaseMessage

type_parsers = {
  UserID: UserID.parse,
  Token: Token.parse,
  # add more types as needed
}


def interface():
    """
    Interface module for handling user interactions and message creation.
    """
    print("Welcome to the Local Social Networking Protocol Interface!")

    while True:
        print("\nSelect an action:")
        for i, (key, value) in enumerate(router.MESSAGE_REGISTRY.items(), start=1):
            print(f"{i}. {key}")
        print(f"{i + 1}. Exit")  # Add exit option at the end

        choice = input("Enter your action number: ").strip()

        if choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(router.MESSAGE_REGISTRY):
                selected_key = list(router.MESSAGE_REGISTRY.keys())[choice_num - 1]

                print(f"\nYou selected: {selected_key}")
                create_message(selected_key)

                
            elif choice_num == len(router.MESSAGE_REGISTRY) + 1:
                print("Exiting. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a valid number.")
        else:
            print("Invalid input. Please enter a number.")



def print_message(msg_obj: BaseMessage):
  """
  Prints the message's payload in a readable format.
  """
  for field, value in msg_obj.payload.items():
    log.debug(f"{field}: {value}")


def create_message(msg_type: str): # ping , dm, profile
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
      log.info(f"TYPE: {value}")
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
            log.warn(f"{e}")
        else:
          new_msg_args[arg_name] = user_input  # fallback or raise error
          break

  new_msg_obj = msg_class(**new_msg_args)
  print_message(new_msg_obj)
  return new_msg_obj

def get_user_id() -> str:
  username = input("Enter username: ")
  user_id = f"{username}@{config.CLIENT_IP}"
  print(f"WELCOME \"{user_id}\"!")
  return user_id