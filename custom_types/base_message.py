from abc import ABC, abstractmethod
import socket
from utils import msg_format

class BaseMessage(ABC):
  """
  Abstract base class for message types.
  Enforces schema presence and requires subclasses to implement
  parsing, receiving, and payload serialization.
  """

  def __init_subclass__(cls):
    super().__init_subclass__()
    if not hasattr(cls, '__schema__'):
      raise TypeError(f"Class {cls.__name__} must define __schema__")
    if not hasattr(cls, '__hidden__'):
      raise TypeError(f"Class {cls.__name__} must define __hidden__")
        
  @classmethod
  @abstractmethod
  def parse(cls, data: dict) -> "BaseMessage":
    """Parses structured data into a message instance"""
    raise NotImplementedError

  def send(self, socket: socket.socket, ip: str, port: int, encoding: str="utf-8"):
    """Sends this message using the provided socket"""
    msg = msg_format.serialize_message(self.payload)
    socket.sendto(msg.encode(encoding), (ip, port))

  @classmethod
  @abstractmethod
  def receive(cls, raw: str) -> "BaseMessage":
    """Receives and parses a message of this type"""
    raise NotImplementedError

  def info(self, verbose: bool = False) -> str:
    """Returns this message's information as a string"""
    if verbose:
      return f"{self.payload}"
    else:
      return f"{self.__class__.__name__}"

  @property
  @abstractmethod
  def payload(self) -> dict:
    """Returns this message's payload in dict form"""
    raise NotImplementedError
