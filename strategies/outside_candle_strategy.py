import backtrader as bt

class CandlestickStrategy(bt.Strategy):
    params = (('wick_thresh', 0.2),)  # Threshold for wick size as a proportion of body

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataOpen= self.datas[0].open
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.order = None  # To keep track of pending orders
        self.sl = None
        self.target = None

    def next(self):
        if self.order:  # Check if an order is pending
            return

        # Access current and previous candle data
        current_open = self.dataOpen[0]
        current_high = self.datahigh[0]
        current_low = self.datalow[0]
        current_close = self.dataclose[0]
        prev_high = self.datahigh[-1]
        prev_low = self.datalow[-1]
        prev_close = self.dataclose[-1]

        # Candlestick conditions for a potential long position (bullish reversal)
        long_condition = (#current_open < current_close and               # Current candle is bullish
                          current_high > prev_high and                  # Current high is higher than the previous high
                          current_low < prev_low and                    # Current low is lower than the previous low
                          current_close < prev_low)                      # Current close is below the previous low

        # Candlestick conditions for a potential short position (bearish reversal)
        short_condition = (#current_open > current_close and              # Current candle is bearish
                           current_low < prev_low and                   # Current low is lower than the previous low
                           current_high > prev_high and                  # Current high is higher than the previous high
                           current_close > prev_high)                    # Current close is above the previous high

        if long_condition:
            self.log('Long signal detected at %.2f' % current_close)
            self.order = self.buy()  # Place a long order

        elif short_condition:
            self.log('Short signal detected at %.2f' % current_close)
            self.order = self.sell()  # Place a short order


