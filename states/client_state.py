import threading
from custom_types.fields import UserID, Token, MessageID
from custom_types.base_message import BaseMessage
from client_logger import client_logger
import time

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
    self._peer_display_names = {}
    self._followers = []
    self._following = []
    self._recent_messages_received = []
    self._recent_messages_sent = []
    self._revoked_tokens = []

  def _validate_user_id(self, data):
    if not isinstance(data, UserID):
      raise ValueError(f"ERROR: {data} is not of type UserID")
    
  def _validate_token(self, data):
    if not isinstance(data, Token):
      raise ValueError(f"ERROR: {data} is not of type Token")
    
  def _validate_base_message(self, data):
    if not isinstance(data, BaseMessage):
      raise ValueError(f"ERROR: {data} is not of type BaseMessage")
  
  def _validate_message_id(self, data):
    if not isinstance(data, MessageID):
        raise ValueError(f"ERROR: {data} is not of type MessageID")
    
  def cleanup_expired_messages(self) -> list[BaseMessage]:
    with self._lock:
      now = int(time.time())
      expired_messages = []
      
      valid_messages_received = []
      for msg in self._recent_messages_received:
        token = getattr(msg, "token", None)
        if token is None or token.valid_until > now:
          valid_messages_received.append(msg)
        else:
          expired_messages.append(msg)
          client_logger.debug(f"EXPIRED: {msg}")
      self._recent_messages_received = valid_messages_received

      valid_messages_sent = []
      for msg in self._recent_messages_sent:
        token = getattr(msg, "token", None)
        if token is None or token.valid_until > now:
          valid_messages_sent.append(msg)
        else:
          expired_messages.append(msg)
          client_logger.debug(f"EXPIRED: {msg}")
      self._recent_messages_sent = valid_messages_sent

      return expired_messages


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

  def update_peer_display_name(self, peer: UserID, display_name: str):
    with self._lock:
      self._validate_user_id(peer)
      if peer not in self._peers:
        self._peers.append(peer)
        client_logger.debug(f"Added peer: {peer}")

      current_name = self._peer_display_names.get(peer)
      if display_name == "":
        if peer in self._peer_display_names:
          del self._peer_display_names[peer]
          client_logger.debug(f"Removed display name for {peer}")
      elif current_name != display_name:
        self._peer_display_names[peer] = display_name
        client_logger.debug(f"Set display name {display_name} for {peer}")

  def get_post_message(self, timestamp) -> "BaseMessage":
    with self._lock:
      for msg in self._recent_messages_sent:
        if msg.type == "POST" and msg.timestamp == timestamp:
            return msg
      return None

  def get_peer_display_name(self, peer: UserID) -> str:
    with self._lock:
      self._validate_user_id(peer)
      if peer in self._peer_display_names:
        return self._peer_display_names[peer]
      return ""
    
  def get_peer_display_names(self) -> dict:
    with self._lock:
      return self._peer_display_names.copy()

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
    
  def add_recent_message_received(self, message: BaseMessage):
    with self._lock:
      msg_token = getattr(message, "token", None)
      if msg_token is None or msg_token not in self._revoked_tokens:
        self._validate_base_message(message)
        self._recent_messages_received.append(message)
      else:
        client_logger.debug("Received message token is revoked.")
  
  def add_recent_message_sent(self, message: BaseMessage):
    with self._lock:
      self._validate_base_message(message)
      self._recent_messages_sent.append(message)


  def get_recent_messages_received(self) -> list:
    self.cleanup_expired_messages()
    with self._lock:
      return self._recent_messages_received
    
  def get_recent_messages_sent(self) -> list:
    with self._lock:
      return self._recent_messages_sent
    
  def revoke_token(self, revoked_token: Token):
    with self._lock:
      self._validate_token(revoked_token)
      valid_messages = []
      for msg in self._recent_messages_received:
        msg_token = getattr(msg, "token", None)
        if msg_token is None or msg_token != revoked_token:
          valid_messages.append(msg)
          continue
        client_logger.debug(f"REVOKE: Invalidating message: {msg}")
        self._revoked_tokens.append(revoked_token)
      self._recent_messages_received = valid_messages

  def get_ack_message(self, message_id) -> "BaseMessage":
    with self._lock:
      self._validate_message_id(message_id)
      for msg in self._recent_messages_received + self._recent_messages_sent:
        try:
          if msg.type == "ACK" and message_id == msg.message_id:
            return msg
        except:
          continue
    
  def get_message_by_id(self, message_id) -> "BaseMessage":
    with self._lock:
      self._validate_message_id(message_id)
      for msg in self._recent_messages_received:
        try:
          if hasattr(msg, "message_id"):
            if message_id == msg.message_id:
              return msg
          elif hasattr(msg, "fileid"):
            if message_id == msg.fileid:
              return msg
        except:
          continue
      return None

  def get_revoked_tokens(self) -> list[Token]:
    with self._lock:
      return self._revoked_tokens

client_state = ClientState()