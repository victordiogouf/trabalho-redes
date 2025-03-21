from reliable_socket import ReliableSocket

def main():
  server = ReliableSocket()
  server.listen('127.0.0.1', 5555)

  print('Connected to client')

  f = open('output.txt', 'wt')
  f.write('')
  f.close()
  
  while True:
    try:
      data = server.receive(10)
      if server.received_fin:
        server.finish()
        print('Waiting for new connection...')
        f = open('output.txt', 'at')
        f.write('\n\n\n\n\n')
        f.close()
        server.listen('127.0.0.1', 5555)
        continue
      f = open('output.txt', 'at')
      f.write(data.decode())
      f.close()

    except KeyboardInterrupt:
      print("\n")
      break

  return

main()