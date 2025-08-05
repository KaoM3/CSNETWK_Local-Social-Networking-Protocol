import socket
import argparse

def main():
  ip = "192.168.5.73"
  port = 50999
  message = "HELLO WORLD!"

  sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sender_socket.sendto(message.encode(), (ip, port))
  sender_socket.close()

  print(f"Sent message to {ip}:{port}")

if __name__ == "__main__":
  main()