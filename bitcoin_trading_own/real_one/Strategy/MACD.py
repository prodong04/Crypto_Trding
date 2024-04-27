import pandas as pd
from typing import Optional

def calculate_macd(df: pd.DataFrame, short_period=12, long_period=26, signal_period=9) -> pd.DataFrame:
    """
    Calculate the Moving Average Convergence Divergence (MACD) indicator and its signal line.

    :param df: DataFrame containing the 'close' price column.
    :param short_period: The short period for the Exponential Moving Average (EMA).
    :param long_period: The long period for the EMA.
    :param signal_period: The period for the signal line.
    :return: DataFrame with MACD and signal line added.
    """
    df['EMA_12'] = df['close'].ewm(span=short_period, adjust=False).mean()
    df['EMA_26'] = df['close'].ewm(span=long_period, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['signal_line'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    df['MACD_diff'] = df['MACD'] - df['signal_line']
    return df

def detect_cross(df: pd.DataFrame, sensitivity=0.01) -> Optional[str]:
    """
    Detects the MACD and signal line cross.

    :param df: DataFrame with MACD and signal line.
    :param sensitivity: The minimum difference to qualify as a cross.
    :return: 'buy' if a bullish cross is detected, 'sell' if a bearish cross is detected, otherwise None.
    """
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    if last_row['MACD_diff'] > sensitivity and prev_row['MACD_diff'] <= sensitivity:
        return 'buy'
    elif last_row['MACD_diff'] < -sensitivity and prev_row['MACD_diff'] >= -sensitivity:
        return 'sell'
    else:
        return 'hold'
    return None

def macd(df: pd.DataFrame, sensitivity=0.01) -> Optional[str]:
    """
    Applies the MACD trading strategy.

    :param df: DataFrame containing the 'close' price column.
    :param sensitivity: The minimum difference between MACD and signal line to qualify as a cross.
    :return: 'buy' or 'sell' signal based on MACD strategy.
    """
    df = calculate_macd(df)
    return detect_cross(df, sensitivity)
