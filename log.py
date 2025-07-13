# Handles logging
# Is the entry point of the application.
# Handles user input as well
import logging

class Color:
    
    SEND = "\033[92m"    # Green
    RECV = "\033[94m"    # Blue
    DROP = "\033[91m"    # Red
    INFO = "\033[96m"    # Cyan
    RESET = "\033[0m"


def setup_logging(verbose):
  global VERBOSE_MODE
  VERBOSE_MODE = verbose

  level = logging.DEBUG if verbose else logging.INFO
  logging.basicConfig(
    level=level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
      logging.FileHandler("app.log"),
      logging.StreamHandler()
    ]
  )

def send(message: str):
  if VERBOSE_MODE:
    logging.debug(f"{Color.SEND}SEND > {message}{Color.RESET}")

def receive(message: str):
  if VERBOSE_MODE:
    logging.debug(f"{Color.RECV}RECV < {message}{Color.RESET}")

def drop(message: str):
  if VERBOSE_MODE:
    logging.debug(f"{Color.DROP}DROP ! {message}{Color.RESET}")


