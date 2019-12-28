import pandas as pd
from datetime import timedelta
from setup import setup
import numpy as np
from plot import plot
import matplotlib.pyplot as plt
from loader import load_index_data
import argparse


parser = argparse.ArgumentParser(description='Plot quotes')
parser.add_argument('--symbol', help='plot only SYMBOL')
args = parser.parse_args()


today, range_dates, conf, prices_manager, all_data, ckp_manager = setup()
zoom_dates = (
    (today - timedelta(days=40)).isoformat(),
    today)

index_symbol = conf.index_symbol()
index_data = load_index_data(prices_manager, index_symbol, range_dates)
index_close = index_data[index_symbol]['Adj Close']
# TODO: plot index

print()
days_range = (20, 90)  # 200)
min_days = 4
if args.symbol is None:
    symbols = all_data.keys()
else:
    symbols = [args.symbol]
for symbol in symbols:
    data = all_data[symbol]
    price = data['Adj Close']

    signals = pd.DataFrame(index=price.index)
    for i in range(days_range[0], days_range[1] + 1):
        col = 'sma_%d' % i
        signals[col] = price.rolling(i).mean()
        col = 'ema_%d' % i
        signals[col] = price.ewm(span=i, adjust=False).mean()

    signals['price'] = price
    positions = pd.DataFrame(index=signals.index).fillna(0)
    short_window = days_range[0]
    long_window = days_range[1]
    ma_short = signals['ema_%d' % short_window]
    ma_long = signals['ema_%d' % long_window]

    signals['signal'] = 0
    signals['signal'][short_window:] = np.where(
        ma_short[short_window:] > ma_long[short_window:],
        1, 0)
    signals['position'] = signals['signal'].diff()

    fig = plot(range_dates, zoom_dates, symbol, data,
               (
                    (price, 'Price'),
                    (ma_short, 'EMA %d' % short_window),
                    (ma_long, 'EMA %d' % long_window),
               ),
               signals)

    plt.savefig('charts/' + symbol + '.png')
    # plt.show()
    plt.close(fig)
