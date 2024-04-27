import pandas as pd
import numpy as np
import time
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

def strategy_macd(df, asset, initiation):
    df = calculate_macd(df)
    cross_positions = detect_cross(df)
    
    df['asset'] = asset
    df['position'] = 'hold'
    
    for date, action in cross_positions:
        df.loc[date, 'position'] = action
    
    return df

def calculate_macd(df):
    df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['signal_line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

def detect_cross(df, sensitivity=0.01):
    cross_positions = []
    for i in range(1, len(df)):
        macd_diff = df['MACD'].iloc[i] - df['signal_line'].iloc[i]
        prev_macd_diff = df['MACD'].iloc[i - 1] - df['signal_line'].iloc[i - 1]

        if macd_diff > sensitivity and prev_macd_diff <= sensitivity:
            cross_positions.append((df.index[i], 'buy'))
        elif macd_diff < -sensitivity and prev_macd_diff >= -sensitivity:
            cross_positions.append((df.index[i], 'sell'))

    return cross_positions

