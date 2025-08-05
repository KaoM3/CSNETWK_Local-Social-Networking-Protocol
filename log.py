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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
      logging.FileHandler("app.log", mode="w"),
    ]
  )

def error(message: str):
    logging.error(message)
    print(f"{Color.ERR}ERROR: {message}{Color.RESET}\n")

def warn(message: str):
    logging.warning(message)
    print(f"{Color.WARN}WARNING: {message}{Color.RESET}\n")

def success(message: str):
    logging.info(message)  # success usually info level
    print(f"{Color.OK}{message}{Color.RESET}\n")

def debug(message: str):
    logging.debug(message)
    print(f"{Color.INFO}{message}{Color.RESET}\n")

def info(message: str):
    logging.info(message)
    print(f"{Color.INFO}{message}{Color.RESET}\n")

def send(message: str):
    logging.info(f"SEND > {message}")
    print(f"{Color.SEND}SEND > {message}{Color.RESET}\n")

def receive(message: str):
    logging.info(f"RECV < {message}")
    print(f"{Color.RECV}RECV < {message}{Color.RESET}\n")

def drop(message: str):
    logging.warning(f"DROP ! {message}")
    print(f"{Color.DROP}DROP ! {message}{Color.RESET}\n")


