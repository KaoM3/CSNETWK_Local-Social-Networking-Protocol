# send_queue.py
import queue
import threading
import client
from client_logger import client_logger

class SendQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.running = False

    def start(self, socket):
        if self.running:
            return
        self.running = True
        thread = threading.Thread(target=self._worker, args=(socket,), daemon=True)
        thread.start()

    def stop(self):
        self.running = False

    def enqueue(self, message, ip, port):
        """Add a message to the queue."""
        self.queue.put((message, ip, port))

    def _worker(self, socket):
        while self.running:
            try:
                message, ip, port = self.queue.get(timeout=1)
                message.send(client.get_, ip=ip, port=port)
                client_logger.debug(f"[Queue] Sent message {message.__class__.__name__} to {ip}:{port}")
            except queue.Empty:
                continue
            except Exception as e:
                client_logger.error(f"[Queue] Error sending message: {e}")

send_queue = SendQueue()