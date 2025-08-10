import os
import base64
import threading
from typing import Dict, List
from custom_types.fields import MessageID
from custom_types.file_transfer import FileTransfer
from client_logger import client_logger

class FileState:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def __init__(self):
        self._initialize()

    def _initialize(self):
        self._lock = threading.RLock()
        self._pending_transfers: Dict[MessageID, FileTransfer] = {}
        self._accepted_files: List[MessageID] = []

        # Save to: <project root>/received_files
        project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        self._files_dir = os.path.join(project_root, "received_files")
        os.makedirs(self._files_dir, exist_ok=True)

    def _validate_message_id(data):
        if not isinstance(data, MessageID):
            raise ValueError(f"{data} is not of type MessageID")
        
    def _validate_file_transfer(data):
        if not isinstance(data, FileTransfer):
            raise ValueError(f"{data} is not of type FileTransfer")

    def accept_file(self, file_id: MessageID):
        with self._lock:
            self._validate_message_id(file_id)
            self._accepted_files.append(file_id)
            client_logger.debug(f"Accepted file transfer with file_id {file_id}")

    def is_file_accepted(self, file_id: MessageID) -> bool:
        with self._lock:
            self._validate_message_id(file_id)
            return file_id in self._accepted_files

    def add_pending_transfer(self, file_id: MessageID, file: FileTransfer):
        with self._lock:
            self._validate_file_transfer(file)
            self._validate_message_id(file_id)
            self._pending_transfers[file_id] = file
            client_logger.debug(f"Accepted pending transfer file {file} with file_id {file_id}")

    def add_chunk(self, file_id: MessageID, chunk_index: int, chunk_data: str) -> bool:
        """Returns True if file is complete after adding chunk"""
        with self._lock:
            if not isinstance(chunk_index, int):
                raise ValueError(f"chunk_index {chunk_index} is not of type int")
            if not isinstance(chunk_data, str):
                raise ValueError(f"chunk_data {chunk_data} is not of type str")
            if file_id not in self._pending_transfers:
                raise ValueError(f"file_id associated with chunk {chunk_data} missing")
            self._validate_message_id(file_id)

            transfer = self._pending_transfers[file_id]
            decoded_data = base64.b64decode(chunk_data)
            transfer.received_chunks[chunk_index] = decoded_data

            if transfer.total_chunks and len(transfer.received_chunks) == transfer.total_chunks:
                self._save_completed_file(file_id)
                return True
            return False

    def _save_completed_file(self, file_id: MessageID):
        transfer = self._pending_transfers[file_id]
        
        # Combine chunks in order
        complete_data = b""
        for i in range(transfer.total_chunks):
            complete_data += transfer.received_chunks[i]

        # Save to file
        filepath = os.path.join(self._files_dir, transfer.filename)
        with open(filepath, "wb") as f:
            f.write(complete_data)

        # Cleanup
        del self._pending_transfers[file_id]
        if file_id in self._accepted_files:
            self._accepted_files.remove(file_id)

file_state = FileState()
