from reliable_socket import ReliableSocket

from socket import socket, AF_INET, SOCK_DGRAM

def main():
  client = socket(AF_INET, SOCK_DGRAM)

  while True:
    input("Press enter to send a message to the server...")
    client.sendto(b'Hello, server!', ('127.0.0.1', 5555))

  # client = ReliableSocket()
  # client.connect('127.0.0.1', 5555)

  # print('Connected to the server')

  # client.send(b'Hello, server!')

main()