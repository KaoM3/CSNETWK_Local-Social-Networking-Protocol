import logging
import threading

class Color:
    OK = "\033[92m"    # Green
    ERR = "\033[91m"   # Red
    INFO = "\033[96m"  # Cyan
    WARN = "\033[93m"  # Yellow
    RECV = "\033[94m"  # Blue
    RESET = "\033[0m"

class ClientLogger:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self, verbose: bool = False):
        self._verbose_mode = verbose
        self._log_lock = threading.Lock()  # <== Lock for print/log-level safety
        level = logging.DEBUG if self._verbose_mode else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("app.log", mode="w"),
            ]
        )

    def set_verbose(self, verbose: bool):
        with self._log_lock:
            self._verbose_mode = verbose
            level = logging.DEBUG if self._verbose_mode else logging.INFO
            logging.getLogger().setLevel(level)

    def print_log(self, message: str, color: Color, non_verbose=False):
        if self._verbose_mode or non_verbose:
            print(f"{color}{message}{Color.RESET}")

    def error(self, message: str):
        with self._log_lock:
            logging.error(message)
            self.print_log(f"ERROR: {message}", Color.ERR, True)

    def warn(self, message: str):
        with self._log_lock:
            logging.warning(message)
            self.print_log(f"WARNING: {message}", Color.WARN, True)

    def success(self, message: str):
        with self._log_lock:
            logging.info(message)
            self.print_log(f"{message}", Color.OK, True)

    def info(self, message: str):
        with self._log_lock:
            logging.info(message)
            self.print_log(f"{message}", Color.INFO, True)

    def debug(self, message: str):
        with self._log_lock:
            logging.debug(message)
            self.print_log(f"{message}", Color.INFO)

    def send(self, message: str):
        with self._log_lock:
            logging.debug(f"SEND > {message}")
            self.print_log(f"SEND > {message}", Color.OK)

    def receive(self, message: str):
        with self._log_lock:
            logging.debug(f"RECV < {message}")
            self.print_log(f"RECV < {message}", Color.RECV)

    def drop(self, message: str):
        with self._log_lock:
            logging.debug(f"DROP ! {message}")
            self.print_log(f"DROP ! {message}", Color.ERR)

    def input(self, prompt: str) -> str:
        with self._log_lock:
            user_input = input(f"{prompt}")
            return user_input

# Global singleton instance
client_logger = ClientLogger()
