from pprint import pprint
from models import Candle
from binance.spot import Spot


class ExchangeClient:
    def market_buy(self, usdt: float) -> (float, float):
        pass

    def market_sell(self, btc: float) -> (float, float):
        pass

    def market_price(self):
        pass


class BinanceTestnetClient(ExchangeClient):
    def __init__(self):
        self.client = Spot(base_url='https://testnet.binance.vision',
                           key='RCJPWEsM8M3GAf3rS9BxmDel4smYUv2ZwGjEVp4aFLi8kc0lguIRKPqrmoZgB2GD',
                           secret='kiqw56MTpd74ARmVl6sX2yYSEZ51PRwx6378RgSRWvWDFMoQumbGohfmq7sEZzsh')

    def candles(self, interval='5m', limit=100):
        b_klines = self.client.klines(symbol='BTCUSDT', interval=interval, limit=limit)
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

    def get_account_assets(self):
        b_account = self.client.account()
        b_balances = b_account['balances']
        return {b_balance['asset']: float(b_balance['free']) for b_balance in b_balances}

    def get_price(self, asset):
        b_price = self.client.ticker_price(symbol=asset)
        return float(b_price['price'])

    def buy_asset(self, asset, amount):
        self.client.new_order(symbol=asset, side='BUY', type='MARKET', quantity=amount)

    def sell_asset(self, asset, amount):
        self.client.new_order(symbol=asset, side='SELL', type='MARKET', quantity=amount)


if __name__ == '__main__':
    client = BinanceTestnetClient()
    pprint(client.get_account_assets())
    pprint(client.candles())
