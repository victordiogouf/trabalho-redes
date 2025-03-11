from struct import pack, unpack

class Packet:
  header_size = 11 # bytes
  max_data_size = 16 # bytes
  max_size = header_size + max_data_size # bytes

  def __init__(self, seq_num: int, ack_num: int, window: int, ack: bool, syn: bool, fin: bool, data: bytes):
    self.seq_num = seq_num
    self.ack_num = ack_num
    self.window = window
    self.ack = ack
    self.syn = syn
    self.fin = fin
    self.data = data

  def __repr__(self): 
    return f'Packet(seq_num={self.seq_num}, ack_num={self.ack_num}, window={self.window}, ack={self.ack}, syn={self.syn}, fin={self.fin}, data={self.data})'
  
  def pack(self):
    flags: int = self.ack << 2 | self.syn << 1 | self.fin
    return pack('!IIHB', self.seq_num, self.ack_num, self.window, flags) + self.data
  
  @staticmethod
  def unpack(b: bytes):
    seq_num, ack_num, window, flags = unpack('!IIHB', b[:11])
    ack = bool(flags >> 2 & 1)
    syn = bool(flags >> 1 & 1)
    fin = bool(flags & 1)
    return Packet(seq_num, ack_num, window, ack, syn, fin, b[11:])