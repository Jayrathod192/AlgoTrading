import pandas as pd
import numpy as np

def total_signal(df, current_candle):
    """
    Generate signals for the given candlestick data based on the strategy.

    Parameters:
        df (DataFrame): The market data containing Open, High, Low, Close columns.
        current_candle (datetime): The current candle's timestamp.

    Returns:
        int: 2 for a long signal, 1 for a short signal, 0 for no signal.
    """
    current_pos = df.index.get_loc(current_candle)

    # Long signal conditions
    c0 = df['Open'].iloc[current_pos] > df['Close'].iloc[current_pos]
    c1 = df['High'].iloc[current_pos] > df['High'].iloc[current_pos - 1]
    c2 = df['Low'].iloc[current_pos] < df['Low'].iloc[current_pos - 1]
    c3 = df['Close'].iloc[current_pos] < df['Low'].iloc[current_pos - 1]
    if c0 and c1 and c2 and c3:
        return 2  # Long signal

    # Short signal conditions
    c0 = df['Open'].iloc[current_pos] < df['Close'].iloc[current_pos]
    c1 = df['Low'].iloc[current_pos] < df['Low'].iloc[current_pos - 1]
    c2 = df['High'].iloc[current_pos] > df['High'].iloc[current_pos - 1]
    c3 = df['Close'].iloc[current_pos] > df['High'].iloc[current_pos - 1]
    if c0 and c1 and c2 and c3:
        return 1  # Short signal

    return 0  # No signal

def add_signals(df):
    """
    Add the signal column to the DataFrame.

    Parameters:
        df (DataFrame): The market data.

    Returns:
        DataFrame: The updated DataFrame with a 'Signal' column.
    """
    df['Signal'] = df.index.map(lambda idx: total_signal(df, idx))
    return df

def add_pointpos(df, signal_column='Signal'):
    """
    Add point positions for visualization purposes.

    Parameters:
        df (DataFrame): The market data with a signal column.
        signal_column (str): The name of the signal column.

    Returns:
        DataFrame: The updated DataFrame with a 'pointpos' column.
    """
    def pointpos(row):
        if row[signal_column] == 2:
            return row['Low'] - 1e-4
        elif row[signal_column] == 1:
            return row['High'] + 1e-4
        else:
            return np.nan

    df['pointpos'] = df.apply(pointpos, axis=1)
    return df
