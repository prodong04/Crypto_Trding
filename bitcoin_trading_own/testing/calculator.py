import pyupbit
import pandas as pd
import numpy as np
import time
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")


def calculate_asset(df, asset, fees):
    status = False

    for i in range(0, len(df)):
        if i == len(df)-1:
            df['asset'].iloc[i] = asset
            break
        ratio = df['open'].iloc[i+1] / df['open'].iloc[i]
        if df['position'].iloc[i] == "buy":
            if not status:
                asset = asset * (1 - fees)
                status = True
                asset = asset * ratio

        elif df['position'].iloc[i] == "sell":
            if status:
                asset = asset * (1 - fees)
                status = False
        elif df['position'].iloc[i] == 0:
            if status:
                asset = asset * ratio

        df['asset'].iloc[i] = asset
        
    return df