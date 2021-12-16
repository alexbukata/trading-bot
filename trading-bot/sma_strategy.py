from __future__ import annotations
from enum import Enum
from technicals import Technicals
from models import Action, Candle
import pandas as pd


def _get_trend(sma14, sma28) -> Trend:
    # if sma14 cross below sma28 -> Trend.UPTREND
    # if sma14 cross above sma28 -> Trend.DOWNTREND
    # else -> Trend.NONE
    changes = zip(sma14, sma28)
    # [false, false, false, true, true, true] - change at index 3, means sma14 cross below sma28
    changes = list(map(lambda x1x2: x1x2[0] > x1x2[1], changes))
    if all(changes):
        return Trend.UPTREND
    if not any(changes):
        return Trend.DOWNTREND
    splits = [[]]
    acc = changes[0]
    for el in changes:
        if el == acc:
            splits[-1].append(el)
        else:
            splits.append([el])
        acc = el
    if len(splits[-1]) < 5:
        return Trend.UNKNOWN
    return Trend.UPTREND if splits[-1][-1] else Trend.DOWNTREND


class State(Enum):
    HOLD = 1
    RELEASE = 2


class Trend(Enum):
    UNKNOWN = 1
    UPTREND = 2
    DOWNTREND = 3


class SmaStrategy:
    def tick(self, candle: Candle) -> (SmaStrategy, Action):
        pass

    @classmethod
    def init(cls, candles) -> SmaStrategy:
        return _Init(Technicals(pd.DataFrame(data=candles)))


class _Init(SmaStrategy):
    def __init__(self, technicals: Technicals):
        self.technicals = technicals

    def tick(self, candle: Candle) -> (SmaStrategy, Action):
        self.technicals.append(candle)
        sma14, sma28 = self.technicals.sma(14), self.technicals.sma(28)
        trend = _get_trend(sma14, sma28)
        if trend == Trend.UPTREND:
            return _Hold(self.technicals, 0), Action.BUY
        if trend == Trend.DOWNTREND:
            return _Release(self.technicals, 0), Action.SELL
        return self, Action.NOTHING


class _Hold(SmaStrategy):
    def __init__(self, technicals: Technicals, wait_counter: int):
        self.technicals = technicals
        self.wait_counter = wait_counter

    def tick(self, candle: Candle) -> (SmaStrategy, Action):
        self.technicals.append(candle)
        if self.wait_counter < 5:
            return _Hold(self.technicals, self.wait_counter + 1), Action.NOTHING
        first_candle = self.technicals.candle_at(-self.wait_counter)
        sma14, sma28 = self.technicals.sma(14), self.technicals.sma(28)
        if first_candle.close + first_candle.close * 0.02 < self.technicals.candle_at(-1).close \
                and sma14[-1] > sma28[-1]:
            return _Hold(self.technicals, 0), Action.BUY
        else:
            return _Init(self.technicals), Action.NOTHING


class _Release(SmaStrategy):
    def __init__(self, technicals: Technicals, wait_counter: int):
        self.technicals = technicals
        self.wait_counter = wait_counter

    def tick(self, candle: Candle) -> (SmaStrategy, Action):
        self.technicals.append(candle)
        if self.wait_counter < 5:
            return _Hold(self.technicals, self.wait_counter + 1), Action.NOTHING
        first_candle = self.technicals.candle_at(-self.wait_counter)
        sma14, sma28 = self.technicals.sma(14), self.technicals.sma(28)
        if first_candle.close - first_candle.close * 0.02 > self.technicals.candle_at(-1).close \
                and sma14[-1] < sma28[-1]:
            return _Release(self.technicals, 0), Action.SELL
        else:
            return _Init(self.technicals), Action.NOTHING
