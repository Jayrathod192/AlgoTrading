import backtrader as bt
import datetime
import pandas as pd
from backtrader import sizers

class SizerPercent(bt.Sizer):
    params = (('percents', 10),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            size = cash * (self.params.percents / 100) / data.close[0]
            return int(size)
        else:
            return self.position.size  # For sells, return existing position size


def run_backtest(cerebro, strategy_cls, data, startdate=None, enddate=None):
    """Runs a backtest."""

    if isinstance(data, pd.DataFrame):
        datafeed = bt.feeds.PandasData(dataname=data)
    else:
        datafeed = data

    cerebro.adddata(datafeed)

    if startdate:

        print('startdate')
        cerebro.broker.setcommission(commission=0.001)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        #cerebro.setdate(dataname=data, fromdate=datetime.datetime.strptime(startdate, "%Y-%m-%d"), todate=datetime.datetime.strptime(enddate, "%Y-%m-%d"))

    #if enddate:
    #   cerebro.setdate(dataname=data, fromdate=datetime.datetime.strptime(startdate, "%Y-%m-%d"), todate=datetime.datetime.strptime(enddate, "%Y-%m-%d"))


    cerebro.addstrategy(strategy_cls)

    cerebro.broker.setcash(100000.0)
    print('backtrader ',type(bt.sizers.FixedSize))
    cerebro.addsizer(bt.sizers.FixedSize,stake=100)
    #print('backtrader ',type(bt.sizers.FixedSize))
    cerebro.addsizer(SizerPercent, percents=50)
    # cerebro.addsizer(bt.sizers.FixedSize(stake=100))
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    results = cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Print analyzers
    #     sharpe = results[0].analyzers.sharpe.get_analysis()
    #     drawdown = results[0].analyzers.drawdown.get_analysis()
    #     returns = results[0].analyzers.returns.get_analysis()
    # Access analyzers by name (assuming newer Backtrader)

    print('result' ,results[0])
    # print('result' ,results[0])
    analyzer_names = results[0].analyzers.getnames()  # Optional: Print available names
    print("Available analyzers:", analyzer_names)
    #print("Available analyzers:", analyzer_names)
    sharpe = results[0].analyzers.getbyname('sharpe').get_analysis()
    drawdown = results[0].analyzers.getbyname('drawdown').get_analysis()
    returns = results[0].analyzers.getbyname('returns').get_analysis()
    # Access the total return using the correct key: 'rtot'
    total_return = returns.get('rtot')
    total_return_percentage = returns.get('rnorm100')
    print("Sharpe Ratio:", sharpe)
    print("Max Drawdown:", drawdown['max']['drawdown'])
    print("Total Return:", total_return)
    print("Total Return Percentage:", total_return_percentage)

    cerebro.plot()
