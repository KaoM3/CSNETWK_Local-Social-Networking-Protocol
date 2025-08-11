import unittest
from unittest.mock import MagicMock
from messages.post import Post
from custom_types.fields import UserID
import socket

class TestPostSend(unittest.TestCase):
    def test_send_broadcasts_to_all_except_sender(self):
        # Arrange
        sender_id = UserID('alice@192.168.1.8', '192.168.1.8')
        post = Post(sender_id, "Hello, world!")

        # Create a mock socket
        mock_sock = MagicMock(spec=socket.socket)
        
        # Act
        post.send(mock_sock, port=37020)



if __name__ == "__main__":
    unittest.main()
