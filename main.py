from socket import socket

class SafeSocket:
  sock: socket
  connection: tuple[str, int] | None

  def __init__(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  # TO DO: Handshake (client side)
  def connect(self, ip: str, port: int): 
    self.connection = (ip, port)

  # TO DO: Handshake (server side)
  def listen(self, ip: str, port: int):
    self.sock.bind((ip, port))  