from datetime import datetime, timezone
from custom_types.fields import UserID, Token, Timestamp, TTL, MessageID
from custom_types.file_transfer import FileTransfer
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from utils.file_transfer import chunk_file, get_file_info
from utils import msg_format
import socket
from client_logger import client_logger
from states.file_state import file_state
from messages.ack import Ack
from messages.file_chunk import FileChunk
import time
import math
import config
import client

class FileOffer(BaseMessage):
    TYPE = "FILE_OFFER"
    SCOPE = Token.Scope.FILE
    __hidden__ = False
    __schema__ = {
        "TYPE": TYPE,
        "FROM": {"type": UserID, "required": True},
        "TO": {"type": UserID, "required": True},
        "FILENAME": {"type": str, "required": True},
        "FILESIZE": {"type": int, "required": True},
        "FILETYPE": {"type": str, "required": True},
        "FILEID": {"type": MessageID, "required": True},
        "DESCRIPTION": {"type": str, "required": True},
        "TIMESTAMP": {"type": Timestamp, "required": True},
        "TOKEN": {"type": Token, "required": True}
    }

    @property
    def payload(self) -> dict:
        payload = {
            "TYPE": self.TYPE,
            "FROM": self.from_user,
            "TO": self.to_user,
            "FILENAME": self.filename,
            "FILESIZE": self.filesize,
            "FILETYPE": self.filetype,
            "FILEID": self.fileid,
            "DESCRIPTION": self.description,
            "TIMESTAMP": self.timestamp,
            "TOKEN": self.token
        }
        return payload

    def __init__(self, to: UserID, filepath: str, description: str = " ", chunk_size: int = 256, ttl: TTL = 3600):
        unix_now = int(datetime.now(timezone.utc).timestamp())
        self.type = self.TYPE
        self.from_user = client_state.get_user_id()
        self.to_user = to
        # Get file info
        try:
            client_logger.debug(f"Getting File Information for {filepath}")
            filename, filesize, filetype = get_file_info(filepath)
            client_logger.debug(f"{filepath}:\nfilename: {filename}\nfilesize: {filesize}\nfiletype: {filetype}")
        except:
            raise ValueError("Filepath is invalid")
        self.filepath = filepath # hidden, not in payload
        self.chunk_size = int(chunk_size)
        self.filename = filename
        self.filesize = filesize
        self.filetype = filetype
        self.total_chunks = math.ceil(self.filesize / self.chunk_size)
        self.fileid = MessageID.generate()
        if description == " ":
            self.description = ""
        else:
            self.description = description
        self.timestamp = Timestamp(unix_now)
        self.token = Token(self.from_user, self.timestamp + ttl, self.SCOPE)

    @classmethod
    def parse(cls, data: dict) -> "FileOffer":
        new_obj = cls.__new__(cls)
        new_obj.type = data["TYPE"]
        new_obj.from_user = UserID.parse(data["FROM"])
        new_obj.to_user = UserID.parse(data["TO"])
        new_obj.filename = str(data["FILENAME"])
        new_obj.filesize = int(data["FILESIZE"])
        new_obj.filetype = str(data["FILETYPE"])
        new_obj.fileid = MessageID.parse(data["FILEID"])
        new_obj.description = data.get("DESCRIPTION", "")
        new_obj.timestamp = Timestamp.parse(int(data["TIMESTAMP"]))
        new_obj.token = Token.parse(data["TOKEN"])
        new_obj.filepath = None
        
        Token.validate_token(new_obj.token, expected_scope=cls.SCOPE, expected_user_id=new_obj.from_user)
        msg_format.validate_message(new_obj.payload, new_obj.__schema__)
        return new_obj

    def send(self, socket: socket.socket, ip: str="default", port: int=50999, encoding: str="utf-8") -> tuple[str, int]:
        if ip == "default":
            ip = self.to_user.get_ip()

        retries = 0
        dest = ("failed", port)
        while retries < 3:
            # Send message
            dest = super().send(socket, ip, port, encoding)
            client_logger.debug(f"Sent file chunk {self.fileid}, attempt {retries + 1}")

            # Wait a bit for ACK
            time.sleep(2)  # Lower this to 0.5 or 1 if latency is tight

            # Check for ACK
            if client_state.get_ack_message(self.fileid) is not None:
                client_logger.debug(f"Received ACK for file {self.fileid}")
                break

            retries += 1
        if dest[0] == "failed":
            client_logger.warn(f"No ACK received for file {self.fileid} after {retries} attempts.")
            return dest

        client.initialize_sockets(config.PORT)
        for i, chunk in enumerate(chunk_file(self.filepath, self.chunk_size)):
            chunk_msg = FileChunk(self.to_user, self.fileid, i, self.total_chunks, self.chunk_size, self.token, chunk)
            chunk_msg.send(client.get_unicast_socket())
            client_logger.info(f"Sent chunk {i+1}/{self.total_chunks}")
            client_logger.send(f"{chunk_msg.payload}")

        return dest

    @classmethod
    def receive(cls, raw: str) -> "FileOffer":
        received = cls.parse(msg_format.deserialize_message(raw))
        if received.to_user != client_state.get_user_id():
            raise ValueError("Message is not intended to be received by this client")
    
        client.initialize_sockets(config.PORT)
        ack = Ack(message_id=received.fileid)
        ack.send(socket=client.get_unicast_socket(), ip=received.from_user.get_ip(), port=config.PORT)

        # Ask user if they want to accept
        #client_logger.info("Someone wants to send you a file! (press enter)")
        #response = client_logger.queue_input(f"User {received.from_user} is sending you a file do you accept? (y/n): ").lower()
        #if response == 'y':
        #    new_transfer = FileTransfer(received.filename, received.filesize, received.filetype)
        #    file_state.add_pending_transfer(received.fileid, new_transfer)
        #    file_state.accept_file(received.fileid)
        
        new_transfer = FileTransfer(received.filename, received.filesize, received.filetype)
        file_state.add_pending_transfer(received.fileid, new_transfer)
        file_state.accept_file(received.fileid)

        return received

    def info(self, verbose: bool = False) -> str:
        if verbose:
            return f"{self.payload}"
        return ""

__message__ = FileOffer