class RttEstimator:
  def __init__(self, alpha = 0.125, beta = 0.25):
    self.estimated_rtt = -1.0
    self.dev_rtt = -1.0
    self.alpha = alpha
    self.beta = beta

  def update(self, sample_rtt: float):
    if self.estimated_rtt == -1.0:
      self.estimated_rtt = sample_rtt
      self.dev_rtt = sample_rtt / 2.0
    else:
      self.dev_rtt = (1.0 - self.beta) * self.dev_rtt + self.beta * abs(sample_rtt - self.estimated_rtt)
      self.estimated_rtt = (1.0 - self.alpha) * self.estimated_rtt + self.alpha * sample_rtt

  def timeout(self):
    return self.estimated_rtt + 4.0 * self.dev_rtt