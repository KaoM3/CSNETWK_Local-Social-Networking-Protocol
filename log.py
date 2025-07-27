import logging
import app

def setup_logging(verbose):
  global VERBOSE_MODE
  VERBOSE_MODE = verbose

  level = logging.DEBUG if verbose else logging.INFO
  logging.basicConfig(
    level=level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
      logging.FileHandler("app.log")
    ]
  )

def error(message: str):
  logging.error(message)
  app.print_log(message)

def warn(message: str):
  logging.warning(message)
  app.print_log(message)

def debug(message: str):
  logging.debug(message)
  app.print_log(message)

def info(message: str):
  logging.info(message)
  app.print_log(message)

def send(message: str):
  logging.info(f"SEND: {message}")
  app.print_log(f"SEND: {message}")

def receive(message: str):
  logging.info(f"RECEIVED: {message}")
  app.print_log(f"RECEIVED: {message}")

def drop(message: str):
  logging.warning(f"DROPPED: {message}")
  app.print_log(f"DROPPED: {message}")


