import datetime

import pandas as pd
import numpy as np
import asyncio
import time
from typing import Dict, List
from models import Candle
from trader import Agent, TradeResult
from binance_api import ExchangeClient, OrderResult, OrderFill
from sma_strategy import SmaStrategy


def _historical():
    df = pd.read_csv("../resources/Bitstamp_BTCUSD_2021_minute.csv", skiprows=1)
    df.drop(['date', 'symbol'], axis=1, inplace=True)
    df.columns = ["unixtimestamp_millis", "open", "high", "low", "close", "volume_btc", "volume_usd"]
    df["unixtimestamp_millis"] = df["unixtimestamp_millis"] * 1000
    df.insert(loc=0, column='datetime', value=pd.to_datetime(df['unixtimestamp_millis'], unit='ms'))
    df = df.iloc[::-1]
    return df


def historical_iter_1m():
    df = _historical()
    df.set_index("datetime", inplace=True)
    df = df.resample("5T").agg({"unixtimestamp_millis": "first",
                                "open": "first",
                                "high": "max",
                                "low": "min",
                                "close": "last",
                                "volume_btc": "sum",
                                "volume_usd": "sum"})
    df.reset_index(inplace=True)
    df["datetime"] = df["datetime"].shift(-1)
    df["unixtimestamp_millis"] = df["unixtimestamp_millis"].shift(-1)
    df = df[:-1]
    df = df.astype({"unixtimestamp_millis": np.int64, "volume_btc": np.int64, "volume_usd": np.int64})
    return df.iterrows()


def historical_iter_5m():
    df = _historical()
    df.set_index("datetime", inplace=True)
    df = df.resample("5T").agg({"unixtimestamp_millis": "first",
                                "open": "first",
                                "high": "max",
                                "low": "min",
                                "close": "last",
                                "volume_btc": "sum",
                                "volume_usd": "sum"})
    df.reset_index(inplace=True)
    df["datetime"] = df["datetime"].shift(-1)
    df["unixtimestamp_millis"] = df["unixtimestamp_millis"].shift(-1)
    df = df[:-1]
    df = df.astype({"unixtimestamp_millis": np.int64, "volume_btc": np.int64, "volume_usd": np.int64})
    return df.iterrows()


def historical_iter_30m():
    df = _historical()
    df.set_index("datetime", inplace=True)
    df = df.resample("30T").agg({"unixtimestamp_millis": "first",
                                 "open": "first",
                                 "high": "max",
                                 "low": "min",
                                 "close": "last",
                                 "volume_btc": "sum",
                                 "volume_usd": "sum"})
    df.reset_index(inplace=True)
    df["datetime"] = df["datetime"].shift(-1)
    df["unixtimestamp_millis"] = df["unixtimestamp_millis"].shift(-1)
    df = df[:-1]
    df = df.astype({"unixtimestamp_millis": np.int64, "volume_btc": np.int64, "volume_usd": np.int64})
    return df.iterrows()


class ExchangeClientMock(ExchangeClient):
    def __init__(self):
        self.curr_price = -1

    def update_price(self, new_price):
        self.curr_price = new_price

    async def market_price(self, asset):
        return self.curr_price

    async def account_assets(self) -> Dict[str, float]:
        pass

    async def buy_asset(self, asset, quoteAmount) -> OrderResult:
        return OrderResult(quoteAmount,
                           quoteAmount,
                           [OrderFill(self.curr_price, quoteAmount / self.curr_price, 0)])

    async def sell_asset(self, asset, assetAmount) -> OrderResult:
        return OrderResult(assetAmount,
                           assetAmount,
                           [OrderFill(self.curr_price, assetAmount, 0)])


class Reporter:
    def __init__(self):
        self.file_path = "../resources/reports/report.csv"
        with open(self.file_path, "w") as csv:
            csv.write("timestamp_millis,btc,overall\n")
        self.buff: List[TradeResult] = []
        self.threshold = 1000

    def report(self, result):
        if result.btc == 0:
            return
        self.buff.append(result)
        if len(self.buff) > 10:
            self.flush()

    def flush(self):
        if len(self.buff) == 0:
            return
        with open(self.file_path, "a") as csv:
            csv.write("\n".join([f"{result.timestamp_millis},{result.btc},{result.overall}" for result in self.buff]))
            csv.write("\n")
            self.buff = []


if __name__ == '__main__':
    async def main():
        reporter = Reporter()
        historical = historical_iter_30m()
        init_candles = [next(historical)[1] for i in range(100)]
        _, raw_candle = next(historical)
        candle = Candle.from_series(raw_candle)
        client = ExchangeClientMock()
        client.update_price(candle.open)
        agent = await Agent.create(client, 0, 50000, SmaStrategy.init(init_candles))
        result: TradeResult = await agent.tick(candle)
        reporter.report(result)
        for _, raw_candle in historical:
            candle = Candle.from_series(raw_candle)
            client.update_price(candle.open)
            # print(candle)
            result: TradeResult = await agent.tick(candle)
            dtm = datetime.datetime.fromtimestamp(candle.timestamp_millis / 1000)
            if dtm.hour == 0 and dtm.minute == 0:
                print(f"Overall: {result.overall}")
            reporter.report(result)
            # time.sleep(0.1)
        reporter.flush()


    asyncio.run(main())
