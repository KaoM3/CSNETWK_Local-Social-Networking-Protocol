class FileTransfer:
  def __init__(self, filename: str, filesize: int, filetype: str, total_chunks: int = 0):
    self.filename = filename
    self.filesize = filesize
    self.filetype = filetype
    self.total_chunks = total_chunks
    self.received_chunks = [None] * total_chunks
    self.received_count = 0
    self._validate()

  def set_total_chunks(self, total_chunks: int):
    self.total_chunks = total_chunks
    self.received_chunks = [None] * self.total_chunks
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

  def __eq__(self, other):
    if not isinstance(other, FileTransfer):
      return NotImplemented
    return (
      self.filename == other.filename and
      self.filesize == other.filesize and
      self.filetype == other.filetype and
      self.total_chunks == other.total_chunks
    )

  def __repr__(self):
    return (
      f"FileTransfer("
      f"filename='{self.filename}', "
      f"filesize={self.filesize}, "
      f"filetype='{self.filetype}', "
      f"received_chunks='{self.received_count}', "
      f"total_chunks={self.total_chunks})"
    )

  def __str__(self):
    return f"{self.filename} ({self.filesize} bytes, {self.total_chunks} chunks)"

  def __hash__(self):
    return hash((self.filename, self.filesize, self.filetype, self.total_chunks))