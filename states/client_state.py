import threading
from custom_types.user_id import UserID
from custom_types.base_message import BaseMessage
from client_logger import client_logger

class ClientState:
  _instance = None
  _lock = threading.RLock()

  def __new__(cls):
    if cls._instance is None:
      with cls._lock:
        if cls._instance is None:
          cls._instance = super().__new__(cls)
          cls._instance._initialize()
    return cls._instance

  def _initialize(self):
    self._lock = threading.RLock()
    self._user_id = None
    self._peers = []
    self._followers = []
    self._following = []
    self._recent_messages = []

  def _validate_user_id(self, data):
    if not isinstance(data, UserID):
      raise ValueError(f"ERROR: {data} is not of type UserID")
    
  def _validate_base_message(self, data):
    if not isinstance(data, BaseMessage):
      raise ValueError(f"ERROR: {data} is not of type BaseMessage")

  def get_user_id(self):
    with self._lock:
      self._validate_user_id(self._user_id)
      return self._user_id

  def set_user_id(self, new_user_id: UserID):
    with self._lock:
      self._user_id = UserID.parse(new_user_id)
      client_logger.debug(f"Set user_id: {self._user_id}")

  def add_peer(self, peer: UserID):
    with self._lock:
      self._validate_user_id(peer)
      if peer not in self._peers:
        self._peers.append(peer)
        client_logger.debug(f"Added peer: {peer}")

  def remove_peer(self, peer: UserID):
    with self._lock:
      self._validate_user_id(peer)
      if peer in self._peers:
        self._peers.remove(peer)
        client_logger.debug(f"Removed peer: {peer}")

  def add_follower(self, follower: UserID):
    with self._lock:
      self._validate_user_id(follower)
      if follower not in self._followers:
        self._followers.append(follower)
        client_logger.debug(f"Added follower: {follower}")

  def remove_follower(self, follower: UserID):
    with self._lock:
      self._validate_user_id(follower)
      if follower in self._followers:
        self._followers.remove(follower)
        client_logger.debug(f"Removed follower: {follower}")

  def add_following(self, target: UserID):
    with self._lock:
      self._validate_user_id(target)
      if target not in self._following:
        self._following.append(target)
        client_logger.debug(f"Added following: {target}")

  def remove_following(self, target: UserID):
    with self._lock:
      self._validate_user_id(target)
      if target in self._following:
        self._following.remove(target)
        client_logger.debug(f"Removed following: {target}")

  def get_peers(self) -> list[UserID]:
    with self._lock:
      return self._peers.copy()
    
  def get_followers(self) -> list[UserID]:
    with self._lock:
      return self._followers.copy()

  def get_following(self) -> list[UserID]:
    with self._lock:
      return self._following.copy()
    
  def add_recent_message(self, message: BaseMessage):
    with self._lock:
      self._validate_base_message(message)
      self._recent_messages.append(message)

  def get_recent_messages(self) -> list:
    with self._lock:
      return self._recent_messages


client_state = ClientState()