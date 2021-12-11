from models import Candle, Action
from sma_strategy import SmaStrategy, init_strategy
import pandas as pd
from backtesting import historical_iter
import time


class ExchangeClient:
    def market_buy(self, usdt: float) -> (float, float):
        pass

    def market_sell(self, btc: float) -> (float, float):
        pass

    def market_price(self):
        pass


class ExchangeClientMock(ExchangeClient):
    def __init__(self):
        self.curr_price = -1

    def update_price(self, new_price):
        self.curr_price = new_price

    def market_buy(self, usdt: float) -> (float, float):
        return usdt / self.curr_price, usdt

    def market_sell(self, btc: float) -> (float, float):
        return btc, btc * self.curr_price

    def market_price(self):
        return self.curr_price


class Agent:
    def __init__(self, client: ExchangeClient, btc, usdt, strategy: SmaStrategy) -> None:
        self.client = client
        self.btc = btc
        self.usdt = usdt
        self.strategy = strategy
        self.orders = []
        print(f"Init capital: {self.overall()} usdt")

    def tick(self, candle: Candle) -> None:
        strategy, action = self.strategy.tick(candle)
        self.strategy = strategy
        if action == Action.NOTHING:
            return
        if action == Action.BUY and self.usdt >= 10:
            btc_bought, usdt_spent = self.client.market_buy(usdt=10)
            self.orders.append((btc_bought, usdt_spent))
            self.btc = self.btc + btc_bought
            self.usdt = self.usdt - usdt_spent
            print(f"bought {btc_bought} btc, spent {usdt_spent} usdt. btc={self.btc}, usdt={self.usdt}. "
                  f"Overall: {self.overall()} usdt")
        elif action == Action.SELL and len(self.orders) > 0:
            btc_bought = sum(map(lambda x: x[0], self.orders))
            btc_spent, usdt_bought = self.client.market_sell(btc=btc_bought)
            self.btc = self.btc - btc_spent
            self.usdt = self.usdt + usdt_bought
            self.orders = []
            print(f"sell {btc_spent} btc, gain {usdt_bought} usdt. btc={self.btc}, usdt={self.usdt}. "
                  f"Overall: {self.overall()} usdt")

    def overall(self):
        return self.btc * self.client.market_price() + self.usdt


if __name__ == '__main__':
    historical = historical_iter()
    init_candles = [next(historical)[1] for i in range(100)]
    _, raw_candle = next(historical)
    candle = Candle.from_series(raw_candle)
    client = ExchangeClientMock()
    client.update_price(candle.close)
    agent = Agent(client, 1, 1000, init_strategy(init_candles))
    agent.tick(candle)
    for _, raw_candle in historical:
        candle = Candle.from_series(raw_candle)
        client.update_price(candle.close)
        # print(candle)
        agent.tick(candle)
        # time.sleep(0.1)
