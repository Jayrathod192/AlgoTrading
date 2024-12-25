from backtesting.backtest_engine import run_backtest
import backtrader as bt
from utils.data_loader import get_historical_data
from strategies.sma_crossover import SmaCross

if __name__ == '__main__':
    #run_backtest()  # Call the backtesting function from backtest_engine.py

    cerebro = bt.Cerebro()
    data = get_historical_data("AAPL", "2020-01-01", "2023-12-25")  # Adjust ticker and date range
    run_backtest(cerebro, SmaCross, data,"2020-01-01","2023-12-25")