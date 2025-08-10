import os
import math
import base64
from datetime import datetime, timezone
from custom_types.fields import UserID, Token, Timestamp, TTL, MessageID
from custom_types.base_message import BaseMessage
from states.client_state import client_state
from client_logger import client_logger
from utils.file_transfer import chunk_file, get_file_info
import config
import inspect

def handle_file_command():
    try:
        # Get file path
        filepath = client_logger.input("Enter file path: ").strip()
        if not os.path.exists(filepath):
            raise ValueError("File does not exist")
            
        # Get recipient
        to_user = UserID.parse(client_logger.input("Send to (user@ip): ").strip())
        description = client_logger.input("Description (optional): ").strip()

        # Get file info
        filename, filesize, filetype = get_file_info(filepath)

        # Get the live UNICAST socket from the running client (__main__)
        import sys
        _main = sys.modules.get("__main__")
        UNICAST_SOCKET = getattr(_main, "UNICAST_SOCKET", None)
        if UNICAST_SOCKET is None:
            raise RuntimeError("UNICAST_SOCKET is not available. Make sure you are running client.py and sockets are initialized.")

        
        # Send offer using router
        import router
        offer = router.send_message(
            UNICAST_SOCKET,
            "FILE_OFFER",
            {
                "to": to_user,
                "filename": filename,
                "filesize": filesize,
                "filetype": filetype,
                "description": description
            },
            to_user.get_ip(),
            config.PORT
        )

        # Send chunks if offer accepted
        if offer:
            client_logger.info("File offer sent, waiting for acceptance...")
            chunk_size = 1024  # 1KB chunks
            total_chunks = math.ceil(filesize / chunk_size)
            
            for i, chunk in enumerate(chunk_file(filepath, chunk_size)):
                chunk_msg = router.send_message(
                    UNICAST_SOCKET,
                    "FILE_CHUNK",
                    {
                        "to": to_user,
                        "fileid": offer.fileid,
                        "chunk_index": i,
                        "total_chunks": total_chunks,
                        "chunk_size": len(chunk),
                        "token": offer.token,
                        "data": chunk
                    },
                    to_user.get_ip(),
                    config.PORT
                )
                client_logger.info(f"Sent chunk {i+1}/{total_chunks}")

            # Send completion message
            complete_msg = router.send_message(
                UNICAST_SOCKET,
                "FILE_RECEIVED",
                {
                    "to": to_user,
                    "fileid": offer.fileid,
                    "status": "COMPLETE"
                },
                to_user.get_ip(),
                config.PORT
            )
            client_logger.info("File transfer completed!")

    except Exception as e:
        client_logger.error(f"File transfer failed: {e}")
