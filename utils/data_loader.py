import yfinance as yf
import pandas as pd
import datetime

def get_historical_data(ticker, start_date, end_date):
    """Downloads historical data from Yahoo Finance."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        #data = yf.download("AMZN AAPL GOOG", start="2023-01-01", end="2023-12-30")

        # Flatten the MultiIndex by taking the second level ('AAPL') and renaming the columns
        data.columns = [col[0] for col in data.columns]  # Extract 'Close', 'High', 'Low', 'Open', 'Volume'

        # Rename columns to match Backtrader's expected format
        data.columns = ['Close', 'High', 'Low', 'open', 'volume']

        if data.empty:
            raise ValueError(f"No data found for ticker: {ticker}")
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