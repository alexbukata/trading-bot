import asyncio
from pprint import pprint
from typing import Callable
from models import Candle
from trader import Agent
from sma_strategy import SmaStrategy
from binance_api import BinanceClient, BinanceSocketProvider

from binance.client import AsyncClient
from binance.streams import BinanceSocketManager
from binance.enums import KLINE_INTERVAL_5MINUTE


async def main():
    client = await BinanceClient.create()
    init_candles = await client.candles()
    init_candles = [candle.to_series() for candle in init_candles]
    agent = await Agent.create(client, 0.5, 1000, SmaStrategy.init(init_candles))
    socket_provider = await BinanceSocketProvider.create()

    async def on_candle(candle: Candle):
        await agent.tick(candle)

    await socket_provider.subscribe_to_klines(on_candle)


if __name__ == '__main__':
    asyncio.run(main())
