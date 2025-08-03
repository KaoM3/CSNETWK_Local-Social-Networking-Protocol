import threading
import log
from custom_types.user_id import UserID

class ClientState:
  _instance = None
  _lock = threading.Lock()

  def __new__(cls):
    if cls._instance is None:
      with cls._lock:
        if cls._instance is None:
          cls._instance = super().__new__(cls)
          cls._instance._init()
    return cls._instance

  def _init(self):
    self._user_id = None
    self._peers = []
    self._followers = []
    self._following = []
    self._lock = threading.Lock()

  def _validate_user_id(self, data):
    if not isinstance(data, UserID):
      raise ValueError(f"ERROR: {data} is not of type UserID")

  def get_user_id(self):
    with self._lock:
      self._validate_user_id(self._user_id)
      return self._user_id

  def set_user_id(self, new_user_id: UserID):
    with self._lock:
      self._user_id = UserID.parse(new_user_id)
      log.info(f"Set user_id: {self._user_id}")

  def add_peer(self, peer: UserID):
    with self._lock:
      self._validate_user_id(peer)
      if peer not in self._peers:
        self._peers.append(peer)
        log.info(f"Added peer: {peer}")

  def remove_peer(self, peer: UserID):
    with self._lock:
      self._validate_user_id(peer)
      if peer in self._peers:
        self._peers.remove(peer)
        log.info(f"Removed peer: {peer}")

  def add_follower(self, follower: UserID):
    with self._lock:
      self._validate_user_id(follower)
      if follower not in self._followers:
        self._followers.append(follower)
        self.add_peer(follower)
        log.info(f"Added follower: {follower}")

  def remove_follower(self, follower: UserID):
    with self._lock:
      self._validate_user_id(follower)
      if follower in self._followers:
        self._followers.remove(follower)
        log.info(f"Removed follower: {follower}")

  def add_following(self, target: UserID):
    with self._lock:
      self._validate_user_id(target)
      if target not in self._following:
        self._following.append(target)
        self.add_peer(target)
        log.info(f"Added following: {target}")

  def remove_following(self, target: UserID):
    with self._lock:
      self._validate_user_id(target)
      if target in self._following:
        self._following.remove(target)
        log.info(f"Removed following: {target}")

  def get_followers(self) -> list[UserID]:
    with self._lock:
      return self._followers.copy()

  def get_following(self) -> list[UserID]:
    with self._lock:
      return self._following.copy()

client_state = ClientState()