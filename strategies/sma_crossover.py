import backtrader as bt

class SmaCross(bt.Strategy):
    params = (('fast', 50), ('slow', 200),)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.sma_fast = bt.indicators.SMA(self.datas[0], period=self.p.fast)
        self.sma_slow = bt.indicators.SMA(self.datas[0], period=self.p.slow)
        self.cross = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)

    def next(self):
        if not self.position:  # Not in the market
            if self.cross > 0:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.buy()
        elif self.cross < 0:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.close()

    #def notify_order(self, order): #added order notification
     #   if order