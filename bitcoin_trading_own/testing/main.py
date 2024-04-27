import pyupbit
import pandas as pd
from pandas.core.frame import DataFrame
import numpy as np
import time
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
from calculator import calculate_asset 
from Strategy.MACD import strategy_macd
from typing import Tuple

warnings.filterwarnings("ignore")

def main(coin: str, interval: str, fees: float, day_count: int, asset: int, initiation: int, K: float) -> DataFrame:
    date = None
    dfs = []

    for i in range(day_count // 200 + 1):
        if i < day_count // 200:
            df = pyupbit.get_ohlcv(coin, to=date, interval=interval)
            date = df.index[0]
        elif day_count % 200 != 0:
            df = pyupbit.get_ohlcv(coin, to=date, interval=interval, count=day_count % 200)
        else:
            break
        dfs.append(df)
        time.sleep(0.1)
    print(dfs)
    if dfs:
        df = pd.concat(dfs).sort_index()
    else:
        df = pd.DataFrame()

    df = strategy_macd(df, asset, initiation)
    df = calculate_asset(df, asset, fees)
    
    first_asset = df['asset'].loc[df['asset'] != 0].iloc[0]
    df['asset_ratio'] = df['asset'] / first_asset
    df['coin_ratio'] = df['open'] / df['open'].iloc[0]
    return df
    
if __name__ == "__main__":
    df = main("KRW-SUI", "minute30", 0.0005, 20, 100000, 5, 0.5)
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['asset_ratio'], label='Asset Ratio', color='blue')
    plt.plot(df.index, df['coin_ratio'], label='Coin Ratio', color='green')
    plt.title('Asset and Coin Ratio Over Time')
    plt.xlabel('Time')
    plt.ylabel('Ratio')
    plt.legend()
    plt.grid(True)
    plt.show()
    print(df[['asset_ratio', 'coin_ratio']])
