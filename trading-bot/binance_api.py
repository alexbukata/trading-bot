from pprint import pprint

from binance.spot import Spot

client = Spot(base_url='https://testnet.binance.vision',
              key='RCJPWEsM8M3GAf3rS9BxmDel4smYUv2ZwGjEVp4aFLi8kc0lguIRKPqrmoZgB2GD',
              secret='kiqw56MTpd74ARmVl6sX2yYSEZ51PRwx6378RgSRWvWDFMoQumbGohfmq7sEZzsh')


def get_account_assets():
    b_account = client.account()
    b_balances = b_account['balances']
    return {b_balance['asset']: float(b_balance['free']) for b_balance in b_balances}


def get_candles():
    b_klines = client.klines(symbol='BTCUSDT', interval='5m', limit=100)
    klines = []
    for b_kline in b_klines:
        klines.append({
            "timestamp_from": float(b_kline[0]),
            "timestamp_to": float(b_kline[6]),
            "open": float(b_kline[1]),
            "high": float(b_kline[2]),
            "low": float(b_kline[3]),
            "close": float(b_kline[4]),
            "asset_volume": float(b_kline[5]),
            "quote_volume": float(b_kline[7])
        })
    return klines


def get_price(asset):
    b_price = client.ticker_price(symbol=asset)
    return float(b_price['price'])


def buy_asset(asset, amount):
    client.new_order(symbol=asset, side='BUY', type='MARKET', quantity=amount)


def sell_asset(asset, amount):
    client.new_order(symbol=asset, side='SELL', type='MARKET', quantity=amount)


if __name__ == '__main__':
    pprint(get_account_assets())
