import pandas as pd
from models import Candle


class Technicals:
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        # self.sma14 = sma(df, 14)
        # self.sma28 = sma(df, 28)
        # self.macd = macd(df)
        # self.obv = obv(df)
        # self.a_d = a_d(df)
        # self.avg_true_range = avg_true_range(df)
        # self.adx = adx(df)
        # self.aroon = aroon(df)
        # self.stochastic = stochastic(df)
        # self.stochastic_sma = stochastic_sma(df)

    def candle_at(self, index):
        return Candle.from_series(self.df.iloc[index])

    def append(self, candle: Candle):
        self.df = self.df.append(candle.to_series(), ignore_index=True)

    def sma(self, period):
        return self.df["close"].rolling(period, min_periods=1).mean()


def ema(df, period):
    return df["close"].ewm(span=period, adjust=False).mean()


def macd(df):
    """
    Name: Moving Average Convergence Divergence
    Покупать, когда MACD пересекает сигнальную линию (9-day EMA) снизу вверх
    Продавать, когда MACD пересекает сигнальную линию (9-day EMA) сверху вниз
    Чем больше таймфрейм, тем меньше ложных сигналов. Час > неделя > месяц
    """
    return ema(df, 12) - ema(df, 26)


def obv(df):
    def obv_value(x):
        if x["close"] > x["close_prev1"]:
            return x["asset_volume"]
        elif x["close"] < x["close_prev1"]:
            return -x["asset_volume"]
        else:
            return 0

    df["close_prev1"] = df.shift(1)["close"]
    return df.apply(obv_value, axis=1).cumsum()


def a_d(df):
    """
    Name: Accumulation/Distribution
    Рост A/D подтверждает восходящий тренд, падение A/D подтверждает нисходящий тренд
    """
    zero_change = df[df["high"] == df["low"]]
    if len(zero_change) != 0:
        print("WARNING! high == low")
        print(zero_change)
    mfm = df.apply(lambda x: ((x["close"] - x["low"]) - (x["high"] - x["close"])) / (x["high"] - x["low"]), axis=1)
    mfv = df["asset_volume"] * mfm
    return mfv.cumsum()


def true_range(df):
    """
    Name: True Range
    Отражает волатильность бумаги
    """
    return pd.DataFrame({
        "0": df["high"] - df["low"],
        "1": (df["high"] - df["close"]).abs(),
        "2": (df["low"] - df["close"]).abs(),
    }).max(axis=1)


def avg_true_range(df):
    """
    Name: Average True Range
    Отражает волатильность бумаги, как и True Range, но сглаживает пики
    """
    return true_range(df).rolling(14, min_periods=1).mean()


def adx(df):
    """
    Name: Average Directional Index
    Показывает силу тренда. Больше 25 - тренд сильный, меньше 20 - слабый
    Также можно использовать для генерации сигналов. Когда +DI пересекает -DI сверху и ADX > 20 (лучше 25),
    то это сигнал к покупке.
    Когда -DI пересекает +DI сверху и ADX >? 20 (лучше 25), то это сигнал к продаже.
    """
    atr = avg_true_range(df)
    df_prev1 = df.shift(1)
    pos_dm = df["high"] - df_prev1["high"]
    sm_pos_dm = pos_dm.rolling(14, min_periods=1).sum() - pos_dm.rolling(14, min_periods=1).mean() + pos_dm
    pos_di = sm_pos_dm / atr * 100
    neg_dm = df["low"] - df_prev1["low"]
    sm_neg_dm = neg_dm.rolling(14, min_periods=1).sum() - neg_dm.rolling(14, min_periods=1).mean() + neg_dm
    neg_di = sm_neg_dm / atr * 100
    dx = 100 * (pos_di - neg_di).abs() / (pos_di + neg_di).abs()
    # Вообще-то ADX считается как (adx_prev * 13 + adx_curr)/14, но делать я так буду только для новых данных
    adx_easy = dx.rolling(14).mean()
    return adx_easy


def aroon(df):
    """
    Name: Aaron Oscillator
    Осциллатор принимает значения от -100 до 100. Близко к 100 - аптренд, близко к -100 - даунтренд
    Когда осциллатор пересекает 0 снизу вверх, значит Aroon Up пересекает Aroon Down снизу вверх, значит максимальных
    цен было больше, что может свидетельствовать о нарастающем аптренде.
    """
    period_since_max = df["high"].rolling(25, min_periods=1).apply(lambda x: x.argmax(), raw=True)
    aaron_up = (25 - period_since_max) / 25 * 100
    period_since_min = df["low"].rolling(25, min_periods=1).apply(lambda x: x.argmin(), raw=True)
    aaron_down = (25 - period_since_min) / 25 * 100
    aaron_osc = aaron_up - aaron_down
    return aaron_osc


def rsi(df):
    """
    Name: Relative Strength Index
    RSI принимает значения от 0 до 100.
    RSI > 70 сигнализирует о перекупленности (значит скоро может быть даунтренд)
    RSI < 30 сигнализирует о перепроданности (значит скоро может быть аптренд)
    """
    gains, losses = (df["close"] - df["open"]) / df["open"] * 100, (df["open"] - df["close"]) / df["open"] * 100
    gains[gains < 0] = 0
    losses[losses < 0] = 0
    return 100 - 100 / (1 + gains.rolling(14).mean() / losses.rolling(14).mean())


def stochastic(df):
    """
    Name: Stochastic Oscillator
    SO принимает значения от 0 до 100.
    SO > 80 сигнализирует о перекупленности (значит скоро может быть медвежий тренд)
    SO < 20 сигнализирует о перепроданности (значит скоро может быть бычий тренд)
    Также когда в бычьем тренде фиксируют новый максимум цены, а SO фиксирует максимумы ниже, то это сигнал о развороте
    тренда
    И наоборот, когда в меджвежьем тренде фиксируют новый минимум цены, а SO фиксирует более высокие максимумы - это
    также сигнал о разовороте тренда
    + Когда SO пересекает SMA(SO, 3) снизу вверх - это бычий сигнал, когда сверху вниз - это медвежий
    """
    close_minus_low = df["close"].shift(1) - df["low"].rolling(14).min()
    high_minus_low = df["high"].rolling(14).max() - df["low"].rolling(14).min()
    so = 100 * close_minus_low / high_minus_low
    return so


def stochastic_sma(so):
    return so.rolling(3).mean()
