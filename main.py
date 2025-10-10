from backtesting.backtest_engine import run_backtest
import backtrader as bt
from utils.data_loader import get_historical_data,load_data_from_csv
from utils.data_loader import load_intraday_data
from strategies.sma_crossover import SmaCross
from strategies.outside_candle_strategy import CandlestickStrategy
from models.trading_model import TradingModel
from fyers_apiv3 import fyersModel
import json

if __name__ == '__main__':
    #run_backtest()  # Call the backtesting function from backtest_engine.py

    cerebro = bt.Cerebro()
    # data = get_historical_data("ADANIPOWER.NS", "2025-01-01", "2025-10-25")  # Adjust ticker and date range
    #data = load_intraday_data("AAPL",'5d','1h')
    data = load_data_from_csv('data/aapl_data.csv')

    client_id = "52GVUJ17IH-100"
    access_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbzU4VGZjMnptYWxjRFhld21jVGtIMUs3dVhkdDB2cGE5SFE2aW1Db29yZnlEVEtyZDRQZm9QZjZoNkFFMkNITkdBdjAtSnhPNVpPUV9SZUNlUU9QZkpOWHdMck56alRRR3hHdnY0QzVEbm04WENnQT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiI1ZDc5ZjMzMDk4NzVjYzhlOGRhMDJlMjVhMTk3Y2QzMmJmMDlmN2UzNGMyNDNhZjI2ZWJmYmZmZiIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFIyMDMyNiIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzYwMDU2MjAwLCJpYXQiOjE3NjAwMTk2NzksImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc2MDAxOTY3OSwic3ViIjoiYWNjZXNzX3Rva2VuIn0.phcLVYoCwAGtnf2NZ1bSnECTjpCUt8Og3QWKV575zQ4'
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

    # data = {"symbol":"NSE:NIFTY50-INDEX","resolution":"5","date_format":"1","range_from":"2025-09-01","range_to":"2025-10-09","cont_flag":"1"}

    # print(fyers.history(data))

    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token,is_async=False, log_path="")
    data = {
        "symbol":"NSE:NIFTY50-INDEX",
        "strikecount":1,
        "timestamp": ""
    }
    response = fyers.optionchain(data=data);
    print(response)


    # run_backtest(cerebro, SmaCross, data)