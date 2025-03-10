from reliable_socket import ReliableSocket

def main():
  client = ReliableSocket()
  client.connect('127.0.0.1', 5555)

  print('Connected to server')

  client.send(b'Hello, server!')

  client.finish()

main()