from reliable_socket import ReliableSocket

from socket import socket, AF_INET, SOCK_DGRAM

def main():
  server = socket(AF_INET, SOCK_DGRAM)

  server.bind(('127.0.0.1', 5555))

  while True:
    input("Press enter to receive a message from the client...") 
    data = server.recvfrom(16)
    print(data)

  # server = ReliableSocket()
  # server.listen('127.0.0.1', 5555)

  # print('Connected to the client')

  # data = server.receive(10000)

  # print(data)
  
main()