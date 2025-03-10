from reliable_socket import ReliableSocket

def main():
  server = ReliableSocket()
  server.listen('127.0.0.1', 5555)

  print('Connected to client')

  while True:
    data = server.receive(10)

    print(data)
  
main()