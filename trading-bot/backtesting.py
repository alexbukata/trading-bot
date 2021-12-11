import pandas as pd
import numpy as np


def historical_iter():
    df_raw = pd.read_csv("../resources/bitstampUSD_1-min_data_2012-01-01_to_2021-03-31.csv")
    df_raw.columns = ["unixtimestamp", "open", "high", "low", "close", "volume_btc", "volume_usd", "weighted_price"]
    df = df_raw.dropna()
    df = df.loc[(df["volume_btc"] > 0) & (df["high"] != df["low"])]
    df.insert(loc=0, column='timestamp', value=pd.to_datetime(df['unixtimestamp'], unit='s'))
    since = np.datetime64("2018-01-01")
    df = df.loc[df["timestamp"] > since]
    df.reset_index(inplace=True, drop=True)
    return df.iterrows()
