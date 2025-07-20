import logging

class Color:
    
    OK = "\033[92m"    # Green
    SEND = "\033[92m"    # Green
    RECV = "\033[94m"    # Blue
    ERR = "\033[91m"    # Red
    DROP = "\033[91m"    # Red
    INFO = "\033[96m"    # Cyan
    WARN = "\033[93m"    # Yellow
    RESET = "\033[0m"


def setup_logging(verbose):
  global VERBOSE_MODE
  VERBOSE_MODE = verbose

  level = logging.DEBUG if verbose else logging.INFO
  logging.basicConfig(
    level=level,
    format='%(message)s',
    handlers=[
      logging.FileHandler("app.log"),
      logging.StreamHandler()
    ]
  )

def error(message: str):
  logging.error(f"{Color.ERR}ERROR: {message}{Color.RESET}")

def warn(message: str):
  logging.warning(f"{Color.WARN}WARNING: {message}{Color.RESET}")

def success(message: str):
  logging.debug(f"{Color.OK}{message}{Color.RESET}")

def debug(message: str):
  logging.debug(f"{Color.INFO}{message}{Color.RESET}")

def info(message: str):
  logging.info(f"{Color.INFO}{message}{Color.RESET}")

def send(message: str):
  logging.debug(f"{Color.SEND}SEND > {message}{Color.RESET}")

def receive(message: str):
  logging.debug(f"{Color.RECV}RECV < {message}{Color.RESET}")

def drop(message: str):
  logging.debug(f"{Color.DROP}DROP ! {message}{Color.RESET}")


