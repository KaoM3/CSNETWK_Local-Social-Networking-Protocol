from custom_types.user_id import UserID

user_id = None

def get_user_id():
  if not isinstance(user_id, UserID):
    raise ValueError(f"ERROR: {user_id} is not of type UserID")
  return user_id

def set_user_id(new_user_id: UserID):
  global user_id
  user_id = UserID.parse(new_user_id)