import yfinance as yf
import pandas as pd
import datetime

def get_historical_data(ticker, start_date, end_date):
    """Downloads historical data from Yahoo Finance."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            raise ValueError(f"No data found for ticker: {ticker}")

        # Rename columns to match Backtrader expectations
        data.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)

        data = data[['open', 'high', 'low', 'close', 'volume']]  # drop Adj Close

        data.index.name = 'datetime'
        return data
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None

def load_data_from_csv(filepath):
    """Loads data from a CSV file."""
    try:
        data = pd.read_csv(filepath, index_col='Date', parse_dates=True)
        return data
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

def load_intraday_data(ticker, period="5d", interval="1h"):  # 1-day range, 1-minute intervals
    try:
        data = yf.download(tickers=ticker, period=period, interval=interval)
        if data.empty:
            raise ValueError(f"No data found for ticker: {ticker}")
        return data
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None

# ... other data loading/preprocessing functions ...