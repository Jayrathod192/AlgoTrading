import backtrader as bt

class SmaCross(bt.Strategy):
    params = (('fast', 21), ('slow', 50), ('main', 200), ('wick_thresh', 0.2))  # Threshold for wick size as a proportion of body

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.high = self.datas[0].high
        self.low = self.datas[0].low
        self.sma_fast = bt.indicators.EMA(self.datas[0], period=self.p.fast)
        self.sma_slow = bt.indicators.EMA(self.datas[0], period=self.p.slow)
        self.sma_main = bt.indicators.EMA(self.datas[0], period=self.p.main)
        self.cross = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
        self.order = None  # To keep track of pending orders

    def next(self):
        if self.order:  # Check if an order is pending
            return

        # Calculate candle body size
        body_size = abs(self.high[0] - self.low[0])

        # Calculate absolute wick sizes (top and bottom)
        upper_wick = abs(self.high[0] - self.sma_fast[0])
        lower_wick = abs(self.low[0] - self.sma_fast[0])

        if self.position.size > 0:  # In a long position
            if self.dataclose[0] < self.sma_slow[0]:
                self.log('SELL CREATE (Long Exit), %.2f' % self.dataclose[0])
                self.order = self.close()

        elif self.position.size < 0:  # In a short position
            if self.dataclose[0] > self.sma_slow[0]:
                self.log('BUY CREATE (Short Exit), %.2f' % self.dataclose[0])
                self.order = self.close()

        elif not self.position:  # Not in any position
            # Long Entry
            if self.dataclose[0] > self.sma_main and self.sma_slow > self.sma_main and self.sma_fast > self.sma_slow:
                if self.cross > 0:# and self.low <= self.sma_fast and self.high > self.sma_fast:
                    # Green candle with small wicks near fast MA
                    self.log('BUY CREATE (Long Entry), %.2f' % self.dataclose[0])
                    self.order = self.buy()

            # Short Entry
            elif self.dataclose[0] < self.sma_main and self.sma_slow < self.sma_main and self.sma_fast < self.sma_slow:
                if self.cross < 0:# and self.low >= self.sma_fast and self.low < self.sma_fast:
                    # Red candle with small wicks near fast MA
                    self.log('SELL CREATE (Short Entry), %.2f' % self.dataclose[0])
                    self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # no pending order
        self.order = None