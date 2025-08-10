import os
import base64
import threading
from typing import Dict, List
from dataclasses import dataclass
from custom_types.fields import MessageID

@dataclass
class FileTransfer:
    filename: str
    total_chunks: int 
    received_chunks: Dict[int, bytes]
    filetype: str
    filesize: int

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

    def accept_file(self, file_id: MessageID):
        with self._lock:
            self._accepted_files.append(file_id)

    def is_file_accepted(self, file_id: MessageID) -> bool:
        with self._lock:
            return file_id in self._accepted_files

    def add_pending_transfer(self, file_id: MessageID, filename: str, total_chunks: int, 
                           filetype: str, filesize: int):
        with self._lock:
            self._pending_transfers[file_id] = FileTransfer(
                filename=filename,
                total_chunks=total_chunks,
                received_chunks={},
                filetype=filetype,
                filesize=filesize
            )

    def add_chunk(self, file_id: MessageID, chunk_index: int, total_chunks: int, chunk_data: str) -> bool:
        """Returns True if file is complete after adding chunk"""
        with self._lock:
            if file_id not in self._pending_transfers:
                return False

            transfer = self._pending_transfers[file_id]

            # If total_chunks wasn't known at offer time, set it from the first chunk
            if not transfer.total_chunks and total_chunks:
                transfer.total_chunks = int(total_chunks)

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
