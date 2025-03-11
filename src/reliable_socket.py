from packet import Packet
from rtt_estimator import RttEstimator

from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime
from threading import Thread, Lock
from random import random

class ReliableSocket:
  def __init__(self):
    self.udp_socket = socket(AF_INET, SOCK_DGRAM)
    self.udp_socket.setblocking(False)
    self.connection: tuple[str, int] | None = None
    self.rtt_estimator = RttEstimator()
    self.timer = datetime.now()
    self.timeout: float | None = None
    self.received: bytes = b''
    self.to_send: bytes = b''
    self.send_base = 1
    self.send_next = 1
    self.send_window = 1
    self.recv_base = 0
    self.recv_window = 100
    self.congestion_window = 1
    self.slow_start_threshold = 8
    self.received_fin = False
    self.syncing = True
    self.synced = False
    self.sent_fin = False
    self.finishing = False
    self.retries = 0
    self.closed = False
    self.loop_thread = Thread(target=self.loop, daemon=True)
    self.lock = Lock()
  
  def connect(self, ip: str, port: int):
    self.connection = (ip, port)
    syn = Packet(self.send_next, 0, self.recv_window, False, True, False, b'')
    self.udp_socket.sendto(syn.pack(), self.connection)
    print('[SEND]', syn)
    self.timer = datetime.now()
    self.timeout = 1.0
    self.loop_thread.start()

    while self.syncing:
      pass

  def listen(self, ip: str, port: int):
    self.udp_socket.bind((ip, port)) 
    self.loop_thread.start()

    while self.syncing:
      pass

  def finish(self):
    if self.closed:
      self.loop_thread.join()
      self.udp_socket.close()
      self.__init__()

    if not self.synced:
      return

    self.finishing = True
    self.retries = 0

    if len(self.to_send) == 0:
      fin = Packet(self.send_base, 0, 0, False, False, True, b'')
      self.udp_socket.sendto(fin.pack(), self.connection)
      print('[SEND]', fin)
      self.sent_fin = True
      self.timeout = 1.0
      self.timer = datetime.now()
    
    # Wait for ack of fin
    while self.finishing:
      pass

    while not self.received_fin:
      pass

    self.closed = True
    self.loop_thread.join()
    self.udp_socket.close()
    self.__init__()
  
  def send(self, data: bytes):
    if not self.synced:
      return

    with self.lock:
      self.to_send += data
      self.send_not_sent()

  def receive(self, size: int):
    while len(self.received) == 0:
      pass

    with self.lock:
      data = self.received[:size]
      self.received = self.received[size:]

    return data

  def send_not_sent(self):
    sent_something = False

    while self.send_next < self.send_base + self.send_window:
      index = self.send_next - self.send_base
      if index == len(self.to_send):
        break
      length = min(Packet.max_data_size, len(self.to_send) - index, self.send_window - index)
      packet = Packet(self.send_next, 0, 0, False, False, False, self.to_send[index:index + length])
      self.udp_socket.sendto(packet.pack(), self.connection)
      print('[SEND]', packet)
      self.send_next += length
      sent_something = True

      if self.timeout is None:
        self.timeout = self.rtt_estimator.timeout()
        self.timer = datetime.now()

    return sent_something

  def check_timeout(self):
    if self.timeout is None:
      return
    
    elapsed = (datetime.now() - self.timer).total_seconds()
    if elapsed < self.timeout:
      return
    
    self.timer = datetime.now()

    if self.syncing or (self.finishing and self.sent_fin):
      self.retries += 1

      if self.retries == 5:
        self.closed = True
        print('Connection timed out while', 'sync' if self.syncing else 'finishing')
        return
      
      self.timeout = min(self.timeout * 2, 30.0)

      if self.syncing:
        syn = Packet(self.send_next, 0, self.recv_window, False, True, False, b'')
        self.udp_socket.sendto(syn.pack(), self.connection)
        print('[SEND]', syn)
      else:
        fin = Packet(self.send_base, 0, 0, False, False, True, b'')
        self.udp_socket.sendto(fin.pack(), self.connection)
        print('[SEND]', fin)

      return
    
    if self.send_window == 0:
      probe = Packet(self.send_base, 0, 0, False, False, False, b'')
      self.udp_socket.sendto(probe.pack(), self.connection)
      print('[SEND]', probe)
      self.timeout = min(self.timeout * 2, 30.0)
      return

    self.slow_start_threshold = self.congestion_window // 2
    self.congestion_window = 1

    self.send_window = min(self.send_window, self.congestion_window)

    index = 0
    max = min(self.send_window, len(self.to_send))
    while index < max:
      length = min(Packet.max_data_size, max - index)
      packet = Packet(self.send_base + index, 0, 0, False, False, False, self.to_send[index:index + length])
      self.udp_socket.sendto(packet.pack(), self.connection)
      print('[SEND]', packet)
      index += length
  
  def receive_packet(self):
    try:
      packet, addr = self.udp_socket.recvfrom(Packet.max_size)
      packet = Packet.unpack(packet)
      # simulate packet loss
      if random() < 0.4:
        print('[LOST]', packet)
        return
      print('[RECV]', packet)
      self.check_packet(packet, addr)
    except (BlockingIOError, ConnectionResetError):
      pass

  def check_packet(self, packet: Packet, addr: tuple[str, int]):
    if self.connection is None:
      if packet.syn:
        self.recv_base = packet.seq_num + len(packet.data)
        self.send_window = min(packet.window, self.congestion_window)

        self.connection = addr
        syn_ack = Packet(self.send_base, self.recv_base, self.recv_window, True, True, False, b'')
        self.udp_socket.sendto(syn_ack.pack(), self.connection)
        print('[SEND]', syn_ack)
        self.timer = datetime.now()
        self.timeout = 1.0
    
    elif addr == self.connection:
      if packet.fin:
        ack = Packet(0, packet.seq_num, 0, True, False, False, b'')
        self.udp_socket.sendto(ack.pack(), self.connection)
        print('[SEND]', ack)
        self.received_fin = True

      elif packet.syn:
        self.recv_base = packet.seq_num
        self.send_window = min(packet.window, self.congestion_window)
        ack = Packet(0, self.recv_base, self.recv_window, True, False, False, b'')
        self.udp_socket.sendto(ack.pack(), self.connection)
        print('[SEND]', ack)

      elif packet.seq_num != 0:
        if packet.seq_num == self.recv_base and len(self.received) < self.recv_window:
          data = packet.data[:self.recv_window - len(self.received)]
          self.received += data
          self.recv_base += len(data)
        
        ack = Packet(0, self.recv_base, self.recv_window - len(self.received), True, False, False, b'')
        self.udp_socket.sendto(ack.pack(), self.connection)
        print('[SEND]', ack)
      
      if packet.ack and packet.ack_num >= self.send_base:
        if self.finishing and self.sent_fin:
          self.finishing = False
          return
        
        num_acked = packet.ack_num - self.send_base
        self.to_send = self.to_send[num_acked:]
        self.send_base = packet.ack_num

        sample_rtt = (datetime.now() - self.timer).total_seconds()
        self.rtt_estimator.update(sample_rtt)

        if self.finishing and len(self.to_send) == 0:
          fin = Packet(self.send_base, 0, 0, False, False, True, b'')
          self.udp_socket.sendto(fin.pack(), self.connection)
          print('[SEND]', fin)
          self.sent_fin = True
          self.timeout = 1.0
          self.timer = datetime.now()
          return
        
        if self.syncing:
          self.syncing = False
          self.synced = True
          self.timeout = None
          return

        if self.congestion_window < packet.window:
          if self.congestion_window < self.slow_start_threshold:
            self.congestion_window *= 2
          else:
            self.congestion_window += 1

        print('packet window:', packet.window, 'Congestion window:', self.congestion_window)  
        self.send_window = min(packet.window, self.congestion_window)

        if self.send_window == 0:
          self.timeout = 1.0
          self.timer = datetime.now()
          return

        if len(self.to_send) == 0:
          self.timeout = None
          return
      
        sent_something = self.send_not_sent()

        if sent_something:
          self.timeout = self.rtt_estimator.timeout()
          self.timer = datetime.now()

  def loop(self):
    while not self.closed:
      with self.lock:
        self.check_timeout()
        self.receive_packet()
