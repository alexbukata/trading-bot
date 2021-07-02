from pprint import pprint
import numpy as np
import time

from binance_api import *


def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w


if __name__ == "__main__":
    while True:
        btc = get_asset_amount('BTC')
        usdt = get_asset_amount('USDT')
        print(f"btc: {btc}, usdt: {usdt}")
        candles = get_candles()
        closes = list(map(lambda x: x['close'], candles))
        sma14 = moving_average(closes, 14)
        sma28 = moving_average(closes, 28)
        price = closes[-1]
        if sma14[-1] > sma28[-1]:
            amount = round(100 / price, 6)
            buy_asset('BTCUSDT', amount)
            print(f"Bought {amount} BTC")
        if sma28[-1] > sma14[-1]:
            amount = round(100 / price, 6)
            sell_asset('BTCUSDT', amount)
            print(f"Sold {amount} BTC")
        time.sleep(60)
