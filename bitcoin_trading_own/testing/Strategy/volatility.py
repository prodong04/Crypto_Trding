
import pyupbit
import pandas as pd
import numpy as np
import time
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")


def strategy_volatility(df, asset, initiation):
    df['range'] = df['high'].shift(1) - df['low'].shift(1)
    df['volatility'] = df['range'].rolling(initiation).mean()
    df['best_K'] = 0.5
    df['asset'] = asset
    df['position'] = 0

    # targetPrice 조절
    df['targetPrice'] = df['open'] + df['volatility'] * df['best_K']*1.5
    df['targetPrice'].iloc[:initiation] = df['open'].iloc[:initiation] 

    # buy/sell 조절
    df['position'] = np.where(df['open'] > df['targetPrice'].shift(1), "buy",
                               np.where(df['open'] < df['targetPrice'].shift(1), "sell",
                                        np.where(df['open'] < 0.97 * df['open'].shift(1), "sell", 0)))

    return df