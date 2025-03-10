from struct import pack, unpack

class Packet:
  header_size = 11 # bytes
  max_data_size = 2 # bytes
  max_size = header_size + max_data_size # bytes

  seq_num: int
  ack_num: int
  window_size: int
  ack: bool
  syn: bool
  fin: bool
  data: bytes

  def __init__(self, seq_num: int, ack_num: int, window_size: int, ack: bool, syn: bool, fin: bool, data: bytes):
    self.seq_num = seq_num
    self.ack_num = ack_num
    self.window_size = window_size
    self.ack = ack
    self.syn = syn
    self.fin = fin
    self.data = data

  def __repr__(self): 
    return f'Packet(seq_num={self.seq_num}, ack_num={self.ack_num}, window_size={self.window_size}, ack={self.ack}, syn={self.syn}, fin={self.fin}, data={self.data})'
  
  def pack(self):
    flags: int = self.ack << 2 | self.syn << 1 | self.fin
    return pack('!IIHB', self.seq_num, self.ack_num, self.window_size, flags) + self.data
  
  @staticmethod
  def unpack(b: bytes):
    seq_num, ack_num, window_size, flags = unpack('!IIHB', b[:11])
    ack = bool(flags >> 2 & 1)
    syn = bool(flags >> 1 & 1)
    fin = bool(flags & 1)
    return Packet(seq_num, ack_num, window_size, ack, syn, fin, b[11:])
  
  @staticmethod
  def split(data: bytes):
    packets: list[Packet] = []
    for i in range(0, len(data), Packet.max_data_size):
      packets.append(Packet(0, 0, 0, False, False, False, data[i:i+Packet.max_data_size]))
    return packets