import math
from pprint import pprint

import matplotlib.pyplot as plt
import numpy as np
import time
import pandas as pd

from binance_api import *
from technicals import *


def make_plot(candles, technicals):
    timestamps = list(map(lambda x: x["timestamp_to"], candles))
    plt.plot(timestamps, list(map(lambda x: x["close"], candles)))
    plt.plot(timestamps, technicals.sma14, color='r')
    plt.plot(timestamps, technicals.sma28, color='g')
    pass


if __name__ == "__main__":
    assets = get_account_assets()
    btc = assets["BTC"]
    usdt = assets["USDT"]
    while True:
        # time.sleep(4 * 60)
        candles = get_candles()
        price = candles[-1]["close"]
        df_candles = pd.DataFrame(data=candles)
        technicals = Technicals(df_candles)
        make_plot(candles, technicals)
        # sma14 < sma28 => sma14 > sma28 - buy
        # sma14 > sma28 => sma14 < sma28 - sell
        prev_signal = "uptrend" if technicals.sma14.iloc[0] > technicals.sma28.iloc[0] else "downtrend"
        curr_signal = "uptrend" if technicals.sma14.iloc[-1] > technicals.sma28.iloc[-1] else "downtrend"
        print(f"prev_signal={prev_signal}, curr_signal={curr_signal}")
        # TODO смотреть в середину. Если есть хоть один перегиб, то тренд меняется, надо торговать
        if prev_signal == curr_signal:
            time.sleep(4 * 60)
            continue
        amount = round(100 / price, 6)
        if prev_signal == "uptrend" and curr_signal == "downtrend":
            if btc > 0:
                print(f"selling {min(amount, btc)} BTC")
                sell_asset('BTCUSDT', min(amount, btc))
        elif prev_signal == "downtrend" and curr_signal == "uptrend":
            if usdt > 101:
                print(f"buying {amount} BTC")
                buy_asset('BTCUSDT', amount)
        time.sleep(4 * 60)
