import backtrader as bt
import pandas as pd
from strategies.signal_utils import add_signals, add_pointpos

class TotalSignalStrategy(bt.SignalStrategy):
    """
    Strategy to implement the 'total_signal' logic for trading.

    This strategy generates long (2) and short (1) signals based on candlestick patterns
    and integrates them into Backtrader.
    """
    def __init__(self):
        # Convert Backtrader data to a pandas DataFrame
        data = {
            "Open": [self.data.open[i] for i in range(len(self.data))],
            "High": [self.data.high[i] for i in range(len(self.data))],
            "Low": [self.data.low[i] for i in range(len(self.data))],
            "Close": [self.data.close[i] for i in range(len(self.data))],
        }
        self.dataframe = pd.DataFrame(data)

        # Generate signals
        self.dataframe = add_signals(self.dataframe)
        self.dataframe = add_pointpos(self.dataframe)

        # Use a pandas DataFrame column as the signal for Backtrader
        self.signal = self.dataframe["Signal"]

    def next(self):
        # Determine the current signal for the current bar
        current_index = len(self) - 1
        if current_index < len(self.signal):
            current_signal = self.signal[current_index]

            if current_signal == 2:  # Long signal
                self.buy()
            elif current_signal == 1:  # Short signal
                self.sell()
