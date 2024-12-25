import yfinance as yf
import pandas as pd
import datetime

def get_historical_data(ticker, start_date, end_date):
    """Downloads historical data from Yahoo Finance."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
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

# ... other data loading/preprocessing functions ...