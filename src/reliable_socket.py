from packet import Packet
from rtt_estimator import RttEstimator

from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime
from threading import Thread, Lock

class ReliableSocket:
  def __init__(self):
    self.sock = socket(AF_INET, SOCK_DGRAM)
    self.sock.setblocking(False)
    self.connection: tuple[str, int] | None = None
    self.rtt_estimator = RttEstimator()
    self.timer = datetime.now()
    self.timeout: float | None = None
    self.received: list[Packet] = []
    self.to_send: list[Packet] = []
    self.send_base = 0
    self.send_next = 0
    self.send_window = -1
    self.recv_base = 0
    self.recv_window = 100
    self.congestion_window = 1
    self.slow_start_threshold = 16
    self.loop_thread = Thread(target=self.loop, daemon=True)
    self.to_send_lock = Lock()
    self.received_lock = Lock()
  
  def connect(self, ip: str, port: int):
    self.connection = (ip, port)
    syn = Packet(self.send_next, 0, self.recv_window, False, True, False, b'')
    self.sock.sendto(syn.pack(), self.connection)
    self.to_send.append(syn)
    self.send_next += 1
    self.loop_thread.start()

    base = self.send_base
    while base == self.send_base:
      pass

  def listen(self, ip: str, port: int):
    self.sock.bind((ip, port)) 
    self.loop_thread.start()

    base = self.send_base
    while base == self.send_base:
      pass

  def finish(self):
    if self.connection is None:
      return

    with self.to_send_lock:
      seq_num = self.send_base + len(self.to_send)
      window_size = self.recv_window - len(self.received)
      fin = Packet(seq_num, 0, window_size, False, False, True, b'')
      self.to_send.append(fin)
      self.send_available()
    
    while self.send_base <= seq_num:
      pass
  
  def send(self, data: bytes):
    if self.connection is None:
      return

    packets = Packet.split(data)

    with self.to_send_lock:
      for packet in packets:
        packet.seq_num = self.send_base + len(self.to_send)
        self.to_send.append(packet);
  
      self.send_available()

  def receive(self, max_packets: int):
    if self.connection is None:
      return

    while len(self.received) == 0:
      pass

    with self.received_lock:
      data = b''
      max = min(max_packets, len(self.received))
      for i in range(max):
        data += self.received[i].data

      self.received = self.received[max:]

    return data

  def send_available(self):
    while self.send_next < self.send_base + self.send_window:
      index = self.send_next - self.send_base
      if index == len(self.to_send):
        break
      print('Sending packet ', self.to_send[index].seq_num)
      self.sock.sendto(self.to_send[index].pack(), self.connection)
      self.send_next += 1

    if self.timeout is None and self.send_window > 0 and len(self.to_send) > 0:
      self.timer = datetime.now()
      self.timeout = 1.0

  def loop(self):
    if self.connection is not None:
      self.timer = datetime.now()
      self.timeout = 1.0

    while True:
      if self.timeout is not None and (datetime.now() - self.timer).total_seconds() > self.timeout:
        self.timer = datetime.now()

        if self.send_window == 0:
          probe = Packet(0, 0, 0, False, False, False, b'')
          self.sock.sendto(probe.pack(), self.connection)
        else:
          self.slow_start_threshold = self.congestion_window // 2
          self.congestion_window = 1

          self.send_window = min(self.send_window, self.congestion_window)

          for i in range(min(self.send_window, len(self.to_send))):
            self.sock.sendto(self.to_send[i].pack(), self.connection)

      try:
        packet, addr = self.sock.recvfrom(Packet.max_size)
      except BlockingIOError:
        continue

      packet = Packet.unpack(packet)

      if self.connection is None:
        if packet.syn:
          self.connection = addr
          self.recv_base = packet.seq_num + 1
          self.send_window = min(packet.window_size, self.congestion_window)

          syn_ack = Packet(self.send_next, packet.seq_num + 1, self.recv_window, True, True, False, b'')
          self.sock.sendto(syn_ack.pack(), self.connection)
          self.to_send.append(syn_ack)
          self.send_next += 1
          self.timer = datetime.now()
          self.timeout = 1.0
      
      elif addr == self.connection:
        if packet.fin:
          ack = Packet(0, packet.seq_num + 1, 0, True, False, False, b'')
          self.sock.sendto(ack.pack(), self.connection)

        elif packet.syn:
          self.recv_base = packet.seq_num + 1
          self.send_window = min(packet.window_size, self.congestion_window)
          ack = Packet(0, packet.seq_num + 1, self.recv_window, True, False, False, b'')
          self.sock.sendto(ack.pack(), self.connection)

        else:
          with self.received_lock:
            if packet.seq_num == self.recv_base:
                self.received.append(packet)
                self.recv_base += 1
            
            ack = Packet(0, self.recv_base, self.recv_window - len(self.received), True, False, False, b'')
            self.sock.sendto(ack.pack(), self.connection)
        
        if packet.ack and packet.ack_num > self.send_base:
          print(f'Packet {packet.ack_num - 1} acked, window size: {packet.window_size}, congestion window: {self.congestion_window}, length of to_send: {len(self.to_send)}')
          with self.to_send_lock:
            num_acked = packet.ack_num - self.send_base
            self.to_send = self.to_send[num_acked:]
            self.send_base = packet.ack_num

            self.send_window = min(packet.window_size, self.congestion_window)

            if self.congestion_window < self.slow_start_threshold:
              self.congestion_window *= 2
            else:
              self.congestion_window += 1

            self.send_available()

            if len(self.to_send) == 0: # All packets acked, just wait for more to send
              self.timeout = None
            elif self.send_window == 0:
              self.timeout = 1.0 # Wait 1.0 sec to send probe
            else:
              sample_rtt = (datetime.now() - self.timer).total_seconds()
              self.rtt_estimator.update(sample_rtt)
              self.timeout = self.rtt_estimator.timeout()
