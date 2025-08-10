class FileTransfer:

  def __init__(self, filename: str, filesize: int, filetype: str, total_chunks: int):
    self.filename = filename
    self.filesize = filesize
    self.filetype = filetype
    self.total_chunks = total_chunks
    self.received_chunks = []
    self._validate()

  def _validate(self):
    if not isinstance(self.filename, str):
      raise ValueError(f"Invalid FileTransfer: filename {self.filename} is not of type str")
    if not isinstance(self.filesize, int):
      raise ValueError(f"Invalid FileTransfer: filesize {self.filesize} is not of type int")
    if not isinstance(self.filetype, str):
      raise ValueError(f"Invalid FileTransfer: filetype {self.filetype} is not of type str")
    if not isinstance(self.total_chunks, int):
      raise ValueError(f"Invalid FileTransfer: total_chunks {self.total_chunks} is not of type int")
