import socket
import argparse

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("ip", help="Destination IP address")
  parser.add_argument("port", type=int, help="Destination port number")
  parser.add_argument("message", help="Message to send")

  args = parser.parse_args()

  sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sender_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  sender_socket.sendto(args.message.encode(), (args.ip, args.port))
  sender_socket.close()

  print(f"Sent message to {args.ip}:{args.port}")

if __name__ == "__main__":
  main()