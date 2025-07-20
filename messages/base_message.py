from abc import ABC, abstractmethod
import socket

class BaseMessage(ABC):
  def __init_subclass__(cls):
    super().__init_subclass__()
    if not hasattr(cls, '__schema__'):
      raise TypeError(f"Class {cls.__name__} must define __schema__")
        
  @classmethod
  @abstractmethod
  def parse(cls, data: dict) -> "BaseMessage":
    """Parses structured data into a message instance"""
    raise NotImplementedError

  def send(self, socket: socket.socket, ip: str, port: int, encoding: str="utf-8"):
    """Sends this message using the provided socket"""
    msg = format.serialize_message(self.payload)
    socket.sendto(msg.encode(encoding), (ip, port))

  @classmethod
  @abstractmethod
  def receive(cls, raw: str) -> "BaseMessage":
    """Receives and parses a message of this type"""
    raise NotImplementedError

  @property
  @abstractmethod
  def payload(self) -> dict:
    """Returns this message's payload in dict form"""
    raise NotImplementedError
