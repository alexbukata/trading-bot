from __future__ import annotations
from pprint import pprint
from typing import Callable, Dict, NamedTuple, List, Coroutine, Any, Awaitable

from models import Candle
from binance.client import AsyncClient
from binance.streams import BinanceSocketManager
from binance.enums import KLINE_INTERVAL_5MINUTE


class OrderFill(NamedTuple):
    price: float
    qty: float
    commission: float


class OrderResult(NamedTuple):
    origQty: float
    executedQty: float
    fills: List[OrderFill]


class ExchangeClient:
    async def account_assets(self) -> Dict[str, float]:
        pass

    async def market_price(self, asset) -> float:
        pass

    async def buy_asset(self, asset, quoteAmount) -> OrderResult:
        pass

    async def sell_asset(self, asset, assetAmount) -> OrderResult:
        pass

    async def test_buy_asset(self, asset, quoteAmount) -> None:
        pass

    async def test_sell_asset(self, asset, quoteAmount) -> None:
        pass


class BinanceClient(ExchangeClient):
    def __init__(self, client: AsyncClient):
        self.client = client

    @classmethod
    async def create(cls) -> BinanceClient:
        client = await AsyncClient.create('RCJPWEsM8M3GAf3rS9BxmDel4smYUv2ZwGjEVp4aFLi8kc0lguIRKPqrmoZgB2GD',
                                          'kiqw56MTpd74ARmVl6sX2yYSEZ51PRwx6378RgSRWvWDFMoQumbGohfmq7sEZzsh',
                                          testnet=True)
        return cls(client)

    async def candles(self, interval=KLINE_INTERVAL_5MINUTE, limit=100):
        b_klines = await self.client.get_klines(symbol='BTCUSDT', interval=interval, limit=limit)
        klines = []
        for b_kline in b_klines:
            klines.append(Candle(
                # float(b_kline[0]),  # timestamp_from
                float(b_kline[6]),  # timestamp_to
                float(b_kline[1]),  # open
                float(b_kline[2]),  # high
                float(b_kline[3]),  # low
                float(b_kline[4]),  # close
                float(b_kline[5]),  # asset_volume
                float(b_kline[7])  # quote_volume
            ))
        return klines

    async def account_assets(self) -> Dict[str, float]:
        b_account = await self.client.get_account()
        b_balances = b_account['balances']
        return {b_balance['asset']: float(b_balance['free']) for b_balance in b_balances}

    async def market_price(self, asset) -> float:
        b_price = await self.client.get_avg_price(symbol=asset)
        return float(b_price['price'])

    async def buy_asset(self, asset, quoteAmount) -> OrderResult:
        res = await self.client.order_market_buy(symbol=asset, quoteOrderQty=quoteAmount)
        return self._order_result(res)

    async def sell_asset(self, asset, assetAmount) -> OrderResult:
        res = await self.client.order_market_sell(symbol=asset, quantity=assetAmount)
        return self._order_result(res)

    @staticmethod
    def _order_result(raw):
        return OrderResult(
            float(raw["origQty"]),
            float(raw["executedQty"]),
            [OrderFill(float(fill["price"]), float(fill["qty"]), float(fill["commission"])) for fill in raw["fills"]]
        )

    async def test_buy_asset(self, asset, quoteAmount) -> Dict:
        return await self.client.create_test_order(symbol=asset, side="BUY", type="MARKET", quoteOrderQty=quoteAmount)

    async def test_sell_asset(self, asset, quoteAmount) -> Dict:
        return await self.client.create_test_order(symbol=asset, side="SELL", type="MARKET", quoteOrderQty=quoteAmount)


class BinanceSocketProvider:
    def __init__(self, client):
        self.client = client
        self.socket_manager = BinanceSocketManager(client)

    @classmethod
    async def create(cls) -> BinanceSocketProvider:
        client = await AsyncClient.create('RCJPWEsM8M3GAf3rS9BxmDel4smYUv2ZwGjEVp4aFLi8kc0lguIRKPqrmoZgB2GD',
                                          'kiqw56MTpd74ARmVl6sX2yYSEZ51PRwx6378RgSRWvWDFMoQumbGohfmq7sEZzsh',
                                          testnet=True)
        return cls(client)

    async def subscribe_to_klines(self, handler: Callable[[Candle], Awaitable[None]]):
        socket = self.socket_manager.kline_socket('BTCUSDT', interval=KLINE_INTERVAL_5MINUTE)
        async with socket as kline_socket:
            while True:
                res = await kline_socket.recv()
                is_candle_final = res["k"]["x"]
                if is_candle_final:
                    await handler(BinanceSocketProvider._socket_response_to_candle(res["k"]))

    @staticmethod
    def _socket_response_to_candle(kline) -> Candle:
        return Candle(
            int(kline["T"]),  # millis
            float(kline["o"]),
            float(kline["h"]),
            float(kline["l"]),
            float(kline["c"]),
            float(kline["v"]),
            float(kline["q"])
        )


if __name__ == '__main__':
    client = BinanceTestnetClient()
    pprint(client.get_account_assets())
    pprint(client.test_buy_asset("BTCUSDT", 100000))
    pprint(client.test_sell_asset("BTCUSDT", 10))
    pprint(client.get_account_assets())
    pprint(client.candles())
