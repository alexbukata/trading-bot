from enum import Enum
from typing import NamedTuple

import pandas as pd


class Action(Enum):
    NOTHING = 1
    BUY = 2
    SELL = 3


class Candle(NamedTuple):
    # timestamp_from: float
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    asset_volume: float
    quote_volume: float

    @staticmethod
    def from_series(raw_candle: pd.Series):
        return Candle(
            raw_candle["unixtimestamp"],
            raw_candle["open"],
            raw_candle["high"],
            raw_candle["low"],
            raw_candle["close"],
            raw_candle["volume_btc"],
            raw_candle["volume_usd"]
        )

    def to_series(self):
        return pd.Series(data={
            "timestamp": pd.to_datetime(self.timestamp, unit='s'),
            "unixtimestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume_btc": self.asset_volume,
            "volume_usd": self.quote_volume
        })
