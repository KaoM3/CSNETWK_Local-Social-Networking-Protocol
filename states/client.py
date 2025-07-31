from custom_types.user_id import UserID
import threading

user_id = None
peers = []
followers = []  # Users following you
following = []  # Users you follow
peers_lock = threading.Lock()

def get_user_id():
    if not isinstance(user_id, UserID):
        raise ValueError(f"ERROR: {user_id} is not of type UserID")
    return user_id

def set_user_id(new_user_id: UserID):
    global user_id
    user_id = UserID.parse(new_user_id)

def add_peer(peer: UserID):
    with peers_lock:
        if not isinstance(peer, UserID):
            raise ValueError(f"ERROR: {peer} is not of type UserID")
        if peer not in peers:
            peers.append(peer)

def remove_peer(peer: UserID):
    with peers_lock:
        if not isinstance(peer, UserID):
            raise ValueError(f"ERROR: {peer} is not of type UserID")
        if peer in peers:
            peers.remove(peer)

def add_follower(follower: UserID):
    with peers_lock:
        if not isinstance(follower, UserID):
            raise ValueError(f"ERROR: {follower} is not of type UserID")
        if follower not in followers:
            followers.append(follower)
            add_peer(follower)

def remove_follower(follower: UserID):
    with peers_lock:
        if not isinstance(follower, UserID):
            raise ValueError(f"ERROR: {follower} is not of type UserID")
        if follower in followers:
            followers.remove(follower)

def add_following(target: UserID):
    with peers_lock:
        if not isinstance(target, UserID):
            raise ValueError(f"ERROR: {target} is not of type UserID")
        if target not in following:
            following.append(target)
            add_peer(target)

def remove_following(target: UserID):
    with peers_lock:
        if not isinstance(target, UserID):
            raise ValueError(f"ERROR: {target} is not of type UserID")
        if target in following:
            following.remove(target)

def get_followers() -> list[UserID]:
    return followers.copy()

def get_following() -> list[UserID]:
    return following.copy()