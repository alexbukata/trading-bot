from models import Candle, Action
from sma_strategy import SmaStrategy
from backtesting import historical_iter
from binance_api import ExchangeClient, OrderResult


# class ExchangeClientMock(ExchangeClient):
#     def __init__(self):
#         self.curr_price = -1
#
#     def update_price(self, new_price):
#         self.curr_price = new_price
#
#     def market_buy(self, usdt: float) -> (float, float):
#         return usdt / self.curr_price, usdt
#
#     def market_sell(self, btc: float) -> (float, float):
#         return btc, btc * self.curr_price
#
#     def market_price(self):
#         return self.curr_price


class Agent:
    def __init__(self, client: ExchangeClient, btc, usdt, strategy: SmaStrategy) -> None:
        self.client = client
        self.btc = btc
        self.usdt = usdt
        self.strategy = strategy
        self.orders = []

    @classmethod
    async def create(cls, client: ExchangeClient, btc, usdt, strategy: SmaStrategy):
        instance = cls(client, btc, usdt, strategy)
        print(f"Init capital: {await instance.overall()} usdt")
        return instance

    async def tick(self, candle: Candle) -> None:
        strategy, action = self.strategy.tick(candle)
        self.strategy = strategy
        if action == Action.NOTHING:
            return
        if action == Action.BUY and self.usdt >= 10:
            order_result: OrderResult = await self.client.buy_asset("BTCUSDT", quoteAmount=10)
            btc_bought = 0
            usdt_spent = 0
            usdt_commission = 0
            for fill in order_result.fills:
                btc_bought += fill.qty
                usdt_spent += fill.qty * fill.price + fill.commission
                usdt_commission += fill.commission
                self.orders.append((fill.qty, fill.price))
            self.btc = self.btc + btc_bought
            self.usdt = self.usdt - usdt_spent
            print(f"bought {btc_bought} btc, spent {usdt_spent} usdt (commission={usdt_commission}). "
                  f"btc={self.btc}, usdt={self.usdt}. Overall: {await self.overall()} usdt")
        elif action == Action.SELL and len(self.orders) > 0:
            btc_bought_already = sum(map(lambda x: x[0], self.orders))
            order_result: OrderResult = await self.client.sell_asset("BTCUSDT", assetAmount=btc_bought_already)
            btc_spent = 0
            usdt_bought = 0
            usdt_commission = 0
            for fill in order_result.fills:
                btc_spent += fill.qty
                usdt_bought += fill.qty * fill.price + fill.commission
                usdt_commission += fill.commission
            self.btc = self.btc - btc_spent
            self.usdt = self.usdt + usdt_bought
            self.orders = []
            print(f"sell {btc_spent} btc, gain {usdt_bought} usdt. btc={self.btc}, usdt={self.usdt}. "
                  f"Overall: {await self.overall()} usdt")

    async def overall(self):
        price = await self.client.market_price("BTCUSDT")
        return self.btc * price + self.usdt


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
