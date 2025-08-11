import os
import time
import base64
import threading
from typing import Dict, List, Optional
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
        self._recent: MessageID = None

        # Save to: <project root>/received_files
        project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        self._files_dir = os.path.join(project_root, "received_files")
        os.makedirs(self._files_dir, exist_ok=True)

    def _validate_message_id(self, data):
        if not isinstance(data, MessageID):
            raise ValueError(f"{data} is not of type MessageID")
        
    def _validate_file_transfer(self, data):
        if not isinstance(data, FileTransfer):
            raise ValueError(f"{data} is not of type FileTransfer")

    def accept_file(self, file_id: MessageID = None):
        with self._lock:
            if file_id is None and self._recent is not None:
                file_id = self._recent
            else:
                raise ValueError("No file transfers to accept")

            self._validate_message_id(file_id)
            if file_id in self._accepted_files:
                client_logger.info(f"File transfer {file_id} already accepted!")
                return
            if file_id not in self._pending_transfers.keys():
                raise ValueError("No pending file offers to accept")

            self._accepted_files.append(file_id)
            client_logger.debug(f"Accepted file transfer with file_id {file_id}")
            transfer = self.get_pending_transfers()[file_id]
            if transfer.received_count == transfer.total_chunks and transfer.total_chunks > 0:
                self._save_completed_file(file_id)
            else:
                client_logger.debug(f"File accepted, but not yet complete: {file_id}")
    
    def reject_file(self, file_id: MessageID = None):
        with self._lock:
            if file_id is None and self._recent is not None:
                file_id = self._recent
            else:
                raise ValueError("No file transfers to reject")
        
            if file_id not in self._pending_transfers.keys():
                    raise ValueError("No pending file offers to reject")
            
            del self._pending_transfers[file_id]


    def is_file_accepted(self, file_id: MessageID) -> bool:
        with self._lock:
            self._validate_message_id(file_id)
            return file_id in self._accepted_files

    def add_pending_transfer(self, file_id: MessageID, file: FileTransfer):
        with self._lock:
            self._validate_file_transfer(file)
            self._validate_message_id(file_id)
            self._pending_transfers[file_id] = file
            self._recent = file_id
            client_logger.debug(f"Added pending transfer file {file} with file_id {file_id}")

    def add_chunk(self, file_id: MessageID, chunk_index: int, chunk_data: str, total_chunks: int) -> bool:
        """Returns True if file is complete after adding chunk"""
        with self._lock:
            if not isinstance(chunk_index, int):
                raise ValueError(f"chunk_index {chunk_index} is not of type int")
            if not isinstance(chunk_data, str):
                raise ValueError(f"chunk_data {chunk_data} is not of type str")
            if not isinstance(total_chunks, int):
                raise ValueError(f"total_chunks {total_chunks} is not of type int")
            if file_id not in self._pending_transfers:
                raise ValueError(f"file_id associated with chunk {chunk_data} missing")
            self._validate_message_id(file_id)

            transfer = self._pending_transfers[file_id]

            if transfer.total_chunks != total_chunks:
                transfer.set_total_chunks(total_chunks)

            decoded_data = base64.b64decode(chunk_data)

            if transfer.received_chunks[chunk_index] is None:
                transfer.received_chunks[chunk_index] = decoded_data
                transfer.received_count += 1
            client_logger.debug(f"Chunks received for FILE_ID {file_id}: {transfer.received_count}")

            if transfer.received_count == transfer.total_chunks:
                client_logger.debug("\n\nALL CHUNKS RECEIVED\n\n")
                return True
            return False

    def _save_completed_file(self, file_id: MessageID):
        transfer = self._pending_transfers[file_id]
        if not (transfer.received_count == transfer.total_chunks and transfer.total_chunks > 0):
            raise ValueError(f"File Transfer with id {file_id} is not yet complete")
        
        # Combine chunks in order
        complete_data = b""
        start_time = time.time()
        prev_time = start_time
        client_logger.process("Combining file chunks...")
        for i in range(transfer.total_chunks):
            chunk = transfer.received_chunks[i]
            if chunk is None:
                raise ValueError(f"Chunk at index {i} is missing or None.")
            complete_data += chunk
            current_time = time.time()
            if current_time - prev_time >= 3:
                client_logger.process(f"completion {(i / transfer.total_chunks) * 100:.2f}%...")
                prev_time = current_time
        client_logger.success("Combined all file chunks!")

        # Save to file
        filepath = os.path.join(self._files_dir, transfer.filename)
        client_logger.process(f"Writing file to {filepath}...")
        with open(filepath, "wb") as f:
            f.write(complete_data)
        client_logger.success(f"File saved to {filepath}!")

        # Cleanup
        del self._pending_transfers[file_id]
        if file_id in self._accepted_files:
            self._accepted_files.remove(file_id)

    def complete_transfers(self):
        with self._lock:
            completed_files = []

            # Work on a copy since we may mutate the list during iteration
            for file_id in list(self._accepted_files):
                if file_id in self._pending_transfers:
                    transfer = self.get_pending_transfers()[file_id]
                    if transfer.received_count == transfer.total_chunks and transfer.total_chunks > 0:
                        self._save_completed_file(file_id)
                    else:
                        client_logger.debug(f"Waiting for {file_id} to complete")

            if completed_files:
                client_logger.debug(f"Completed file transfers: {completed_files}")

    def remove_transfers(self, file_ids: list[MessageID]):
        with self._lock:
            for file_id in file_ids:
                removed = False

                if file_id in self._accepted_files:
                    self._accepted_files.remove(file_id)
                    client_logger.debug(f"Removed file_id {file_id} from accepted files")
                    removed = True

                if file_id in self._pending_transfers:
                    del self._pending_transfers[file_id]
                    client_logger.debug(f"Removed file_id {file_id} from pending transfers")
                    removed = True

                if not removed:
                    client_logger.warn(f"Tried to remove non-existent file_id {file_id}")

    def get_recent(self) -> Optional[MessageID]:
        return self._recent
    
    def get_pending_transfers(self) -> Dict[MessageID, FileTransfer]:
        return self._pending_transfers

    def get_accepted_files(self) -> list[MessageID]:
        return self._accepted_files

file_state = FileState()
