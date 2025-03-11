import backtrader as bt
import datetime
import pandas as pd
from backtrader import sizers
from fyers_apiv3 import fyersModel
class SizerPercent(bt.Sizer):
    params = (('percents', 10),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            size = cash * (self.params.percents / 100) / data.close[0]
            return int(size)
        else:
            return self.position.size  # For sells, return existing position size

def process_fyers_data(fyers_data):
    """
    Convert Fyers API historical data into a Pandas DataFrame.

    Parameters:
        fyers_data (dict): Historical data from Fyers API with 'candles'.

    Returns:
        pd.DataFrame: Processed OHLCV data with a DateTime index.
    """
    candles = fyers_data.get('candles', [])
    df = pd.DataFrame(
        candles,
        columns=['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']
    )
    # Convert timestamp to datetime
    df['DateTime'] = pd.to_datetime(df['DateTime'], unit='s')
    df.set_index('DateTime', inplace=True)
    return df

def run_backtest(cerebro, strategy_cls, data, startdate=None, enddate=None,isFyersData=False):
    """Runs a backtest."""


    if isFyersData:
        data_df = process_fyers_data(data)

    else:
        if isinstance(data, pd.DataFrame):

            datafeed = bt.feeds.PandasData(dataname=data)
        else:
            datafeed = data

    # Filter data for the backtest period if dates are provided
    if startdate and enddate:
        data_df = data_df.loc[startdate:enddate]

    # Convert DataFrame to Backtrader DataFeed
    datafeed = bt.feeds.PandasData(dataname=data_df)

    cerebro.adddata(datafeed)

    if startdate:
        cerebro.broker.setcommission(commission=0.001)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        #cerebro.setdate(dataname=data, fromdate=datetime.datetime.strptime(startdate, "%Y-%m-%d"), todate=datetime.datetime.strptime(enddate, "%Y-%m-%d"))

    #if enddate:
     #   cerebro.setdate(dataname=data, fromdate=datetime.datetime.strptime(startdate, "%Y-%m-%d"), todate=datetime.datetime.strptime(enddate, "%Y-%m-%d"))


    cerebro.addstrategy(strategy_cls)

    cerebro.broker.setcash(100000.0)
  #  print('backtrader ',type(bt.sizers.FixedSize))
    cerebro.addsizer(bt.sizers.FixedSize,stake=100)
    #print('backtrader ',type(bt.sizers.FixedSize))
    cerebro.addsizer(SizerPercent, percents=30)
   # cerebro.addsizer(bt.sizers.FixedSize(stake=100))
    start_value = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    results = cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    end_value = cerebro.broker.getvalue()

    # Print analyzers
#     sharpe = results[0].analyzers.sharpe.get_analysis()
#     drawdown = results[0].analyzers.drawdown.get_analysis()
#     returns = results[0].analyzers.returns.get_analysis()
    # Access analyzers by name (assuming newer Backtrader)

    #print('result' ,results[0])
   # print('result' ,results[0])
    analyzer_names = results[0].analyzers.getnames()  # Optional: Print available names
   # print("Available analyzers:", analyzer_names)
    #print("Available analyzers:", analyzer_names)
    sharpe = results[0].analyzers.getbyname('sharpe').get_analysis()
    drawdown = results[0].analyzers.getbyname('drawdown').get_analysis()
    returns = results[0].analyzers.getbyname('returns').get_analysis()
    # Access the total return using the correct key: 'rtot'
    total_return = returns.get('rtot')
    total_return_percentage = returns.get('rnorm100')
    print("Sharpe Ratio:", sharpe)
    print("Max Drawdown:", drawdown['max']['drawdown'])
    print("Total Return:", round(end_value -start_value))
    print("Total Return Percentage:",( (end_value -start_value) * 100)/start_value)




    # cerebro.plot(style='candlestick')
