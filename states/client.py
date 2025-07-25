from custom_types.user_id import UserID

user_id = None
peers = []

def get_user_id():
  if not isinstance(user_id, UserID):
    raise ValueError(f"ERROR: {user_id} is not of type UserID")
  return user_id

def set_user_id(new_user_id: UserID):
  global user_id
  user_id = UserID.parse(new_user_id)

def add_peer(peer: UserID):
  if not isinstance(peer, UserID):
    raise ValueError(f"ERROR: {peer} is not of type UserID")
  if peer in peers:
    raise ValueError(f"ERROR: {peer} already in peers")
  peers.append(peer)

def remove_peer(peer: UserID):
  if not isinstance(peer, UserID):
    raise ValueError(f"ERROR: {peer} is not of type UserID")
  if peer not in peers:
    raise ValueError(f"ERROR: {peer} not found in peers")
  peers.remove(peer)