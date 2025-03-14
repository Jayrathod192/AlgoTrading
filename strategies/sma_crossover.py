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
        self.sl = None
        self.target = None

    def next(self):
        if self.order:  # Check if an order is pending
            return

        # Calculate candle body size
        body_size = abs(self.high[0] - self.low[0])

        # Calculate absolute wick sizes (top and bottom)
        upper_wick = abs(self.high[0] - self.sma_fast[0])
        lower_wick = abs(self.low[0] - self.sma_fast[0])

        if self.position.size > 0:  # In a long position
            if self.dataclose[0] < self.sma_slow[0] or self.dataclose[0] <= self.sl: #or self.dataclose[0] >= self.target:
                self.log('SELL CREATE (Long Exit), %.2f' % self.dataclose[0])
                self.order = self.close()

        elif self.position.size < 0:  # In a short position
            if self.dataclose[0] > self.sma_slow[0]:
                self.log('BUY CREATE (Short Exit), %.2f' % self.dataclose[0])
                self.order = self.close()

        elif not self.position:  # Not in any position
            # Long Entry
            # Long Entry Condition
            if self.dataclose[0] > self.sma_main[0] and self.sma_fast[0] > self.sma_slow[0] and self.sma_slow[0] > self.sma_main[0]:
                # Ensure price is above the 21 EMA and the EMAs are in correct order (21 > 50 > 200)
                if self.low[0] <= self.sma_fast[0] and self.dataclose[0] > self.sma_fast[0]:

                    self.sl = self.low[0]
                    self.target = self.high[0] + (2 * (self.high[0] - self.sl))

                    self.log('BUY CREATE (Long Entry), %.2f' % self.high[0])
                    self.order = self.buy(
                        price=self.high[0],
                        trailpercent = 1)

            # Short Entry Condition
            elif self.dataclose[0] > self.sma_main[0] and self.sma_fast[0] < self.sma_slow[0] and self.sma_slow[0] < self.sma_main[0]:
                # Ensure price is above the 200 EMA and the EMAs are in correct order (21 < 50 < 200)
                if self.high[0] >= self.sma_fast[0] and self.dataclose[0] < self.sma_fast[0]:
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
                    (order.price,
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