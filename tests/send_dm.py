import socket
import sys
import log
from messages import dm as dm

def main():
  if len(sys.argv) < 4:
    print("Usage: python send_dm.py <from_user> <to_user> <message>")
    sys.exit(1)

  from_user = sys.argv[1]
  to_user = sys.argv[2]
  content = " ".join(sys.argv[3:])

  # Create a UDP socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  try:
    dm.send(sock, from_user, to_user, content)
    print("DM sent successfully.")
  except Exception as e:
    print(f"Failed to send DM: {e}")


if __name__ == "__main__":
  main()

# e.g. python send_dm.py alice@192.168.1.11 bob@192.168.1.12 "Hello Bob!"