import os
from typing import Generator

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
    
    # Simple filetype detection
    ext = os.path.splitext(filename)[1].lower()
    filetypes = {
        '.txt': 'text/plain',
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg', 
        '.png': 'image/png',
        '.gif': 'image/gif'
    }
    filetype = filetypes.get(ext, 'application/octet-stream')
    
    return filename, filesize, filetype
