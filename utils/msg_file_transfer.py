from typing import Generator
import mimetypes
import os

def chunk_file(filepath: str, chunk_size: int = 1024) -> Generator[bytes, None, None]:
    """Generator that yields file chunks of specified size"""
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def get_file_info(filepath: str) -> tuple[str, int, str]:
    """Returns (filename, filesize, filetype)"""
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    filetype, _ = mimetypes.guess_type(filename)
    return filename, filesize, filetype or 'application/octet-stream'
