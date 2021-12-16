from typing import NamedTuple, List

from models import Candle, Action
from sma_strategy import SmaStrategy
from binance_api import ExchangeClient, OrderResult, OrderFill


class TradeResult(NamedTuple):
    timestamp_millis: float
    btc: float
    usdt: float
    commission: float
    overall: float


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
        print(f"Init assets: {await client.account_assets()}")
        print(f"Init capital: {await instance.overall()} usdt")
        return instance

    async def tick(self, candle: Candle) -> TradeResult:
        # print("================")
        strategy, action = self.strategy.tick(candle)
        self.strategy = strategy
        # print(f"Action: {action}")
        if action == Action.BUY and self.usdt >= 100:
            order_result: OrderResult = await self.client.buy_asset("BTCUSDT", quoteAmount=100)
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
            # print(f"bought {btc_bought} btc, spent {usdt_spent} usdt (commission={usdt_commission}). "
            #       f"btc={self.btc}, usdt={self.usdt}. Overall: {await self.overall()} usdt")
            return TradeResult(candle.timestamp_millis, btc_bought, -usdt_spent, usdt_commission, await self.overall())
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
            # print(f"sell {btc_spent} btc, gain {usdt_bought} usdt. btc={self.btc}, usdt={self.usdt}. "
            #       f"Overall: {await self.overall()} usdt")
            return TradeResult(candle.timestamp_millis, -btc_spent, usdt_bought, usdt_commission, await self.overall())
        else:
            return TradeResult(candle.timestamp_millis, 0, 0, 0, await self.overall())

    async def overall(self):
        price = await self.client.market_price("BTCUSDT")
        return self.btc * price + self.usdt
