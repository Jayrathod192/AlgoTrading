from backtesting.backtest_engine import run_backtest
import backtrader as bt
from utils.data_loader import get_historical_data,load_data_from_csv
from utils.data_loader import load_intraday_data
from strategies.sma_crossover import SmaCross
from strategies.outside_candle_strategy import CandlestickStrategy
from models.trading_model import TradingModel
from fyers_apiv3 import fyersModel

if __name__ == '__main__':
    #run_backtest()  # Call the backtesting function from backtest_engine.py

    cerebro = bt.Cerebro()
    # data = get_historical_data("infy.ns", "2020-01-01", "2024-10-25")  # Adjust ticker and date range
    #data = load_intraday_data("AAPL",'5d','1h')
    #data = load_data_from_csv('data/aapl_data.csv')

    client_id = "52GVUJ17IH-100"
    access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3MzYwNzk0ODAsImV4cCI6MTczNjEyMzQwMCwibmJmIjoxNzM2MDc5NDgwLCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbmVuaDRoWUxuMWVJRTlqblFoUnFGM19EV0sxTWxVdWxlRGx0cDl3dTRQWllNYWQtRDUxRndqVzMyVEJURGp0eU1wYkhDczJueXRyRVMwMHdra0laSVFSNXYtWWh4eWdJOHFEdTBhYlgzYm9Fcjd4OD0iLCJkaXNwbGF5X25hbWUiOiJSYXRob2QgSmlnbmVzaCIsIm9tcyI6IksxIiwiaHNtX2tleSI6bnVsbCwiZnlfaWQiOiJYUjIwMzI2IiwiYXBwVHlwZSI6MTAwLCJwb2FfZmxhZyI6Ik4ifQ.3erfpr8z43COJMFu4nTnetVBb8BowLkMj1WP5Km1K6w'
    fyers = fyersModel.FyersModel(token=access_token,is_async=False,client_id=client_id,log_path="")


# Initialize the trading model
    # trading_model = TradingModel()

    # Train the model on the historical stock data
    # trading_model.train(data)

    # run_backtest(cerebro, SmaCross, data,"2020-01-01", "2023-12-25")

    # Train the model
    #trading_model = TradingModel()
    #trading_model.train(data)

    # Add SmaCross strategy

    # cerebro.addstrategy(SmaCross)

    # Add the model filter strategy that uses the trained model
    # cerebro.addstrategy(SmaCross, model=trading_model)

    data = {"symbol":"NSE:techm-EQ","resolution":"D","date_format":"1","range_from":"2024-01-01","range_to":"2024-12-31","cont_flag":"1"}

    # print(fyers.history(data))

    run_backtest(cerebro, SmaCross, fyers.history(data), "2024-01-01", "2024-12-31",'true')