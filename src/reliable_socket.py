from packet import Packet, g_max_packet_size

from datetime import datetime
from socket import socket, timeout, AF_INET, SOCK_DGRAM

g_sync_timeout = 1.0 # seconds

class ReliableSocket:
  sock: socket
  connection: tuple[str, int] | None
  estimated_rtt: float
  dev_rtt: float
  send_base: int
  recv_base: int
  recv_window: int

  def __init__(self):
    self.sock = socket(AF_INET, SOCK_DGRAM)
    self.connection = None
    self.estimated_rtt = -1.0
    self.dev_rtt = -1.0
    self.send_base = 0
    self.recv_base = 0
    self.recv_window = 1
  
  def connect(self, ip: str, port: int): 
    syn = Packet(self.send_base, 0, 0, False, True, False, b'')
    self.sync(syn, (ip, port))

  def listen(self, ip: str, port: int):
    self.sock.bind((ip, port)) 
    self.sock.settimeout(None)

    while True:
      received, addr = self.sock.recvfrom(16)
      received = Packet.unpack(received)

      if received.syn:
        self.recv_base = received.seq_num + 1
        syn_ack = Packet(self.send_base, received.seq_num + 1, 0, True, True, False, b'')
        self.sync(syn_ack, addr)
        break
  
  def sync(self, syn: Packet, target: tuple[str, int]):
    self.sock.sendto(syn.pack(), target)
    self.sock.settimeout(g_sync_timeout)
    start = datetime.now()

    while self.connection is None:
      try:
        received, addr = self.sock.recvfrom(16)

        if addr != target:
          continue

        received = Packet.unpack(received)

        if received.ack and received.ack_num == self.send_base + 1:
          self.connection = addr
          self.estimated_rtt = (datetime.now() - start).total_seconds()
          self.dev_rtt = 0.25 * self.estimated_rtt
          self.send_base += 1

          if received.syn:
            self.recv_base = received.seq_num + 1
            ack = Packet(0, received.seq_num + 1, 0, True, False, False, b'')
            self.sock.sendto(ack.pack(), addr)

      except timeout:
        self.sock.sendto(syn.pack(), target)

        curr = self.sock.gettimeout()
        self.sock.settimeout(curr * 2)
        start = datetime.now()

  def send(self, data: bytes):
    if not self.connection:
      raise Exception('No connection established')

    packets = Packet.split(data)

    for i in range(min(self.recv_window, len(packets))): # change to min(self.recv_window, self.congestion_window)
      packets[i].seq_num = self.send_base + i
      self.sock.sendto(packets[i].pack(), self.connection)

    local_base = 0
    next_seq_num = self.recv_window

    self.sock.settimeout(self.estimated_rtt + 4 * self.dev_rtt)
    start = datetime.now()

    while local_base < len(packets):
      try:
        received, addr = self.sock.recvfrom(g_max_packet_size)

        if addr != self.connection:
          continue

        received = Packet.unpack(received)

        if received.ack and received.ack_num > self.send_base:
          diff = received.ack_num - self.send_base
          local_base += diff
          self.recv_window = received.window_size
          self.send_base = received.ack_num
          self.estimated_rtt = 0.875 * self.estimated_rtt + 0.125 * (datetime.now() - start).total_seconds()
          self.dev_rtt = 0.75 * self.dev_rtt + 0.25 * abs((datetime.now() - start).total_seconds() - self.estimated_rtt)
          self.sock.settimeout(self.estimated_rtt + 4 * self.dev_rtt)

      except timeout:
        for i in range(local_base, min(local_base + self.recv_window, len(packets))):
          packets[i].seq_num = self.send_base + i
          self.sock.sendto(packets[i].pack(), self.connection)
        
        curr = self.sock.gettimeout()
        self.sock.settimeout(curr * 2)
        start = datetime.now()

  def receive(self, max_packets: int):
    if not self.connection:
      raise Exception('No connection established')
    
    data = b''
    packets = 0

    self.sock.settimeout(None)

    while packets < max_packets:
      received, addr = self.sock.recvfrom(g_max_packet_size)

      if addr != self.connection:
        continue

      received = Packet.unpack(received)

      if received.seq_num == self.recv_base:
        data += received.data
        self.recv_base += 1
        packets += 1

      ack = Packet(0, self.recv_base, max_packets - packets, True, False, False, b'')
      self.sock.sendto(ack.pack(), addr)

    return data
