from reliable_socket import ReliableSocket

def main():
  client = ReliableSocket()
  client.connect('127.0.0.1', 5555)

  print('Connected to server')

  f = open('../input.txt', 'rt', encoding='utf-8')
  data = f.read()
  f.close()
  client.send(data.encode())
  print('Data sent')
  client.finish()
  print("Fim da conexão")
  return

main()