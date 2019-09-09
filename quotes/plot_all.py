import pandas as pd
import matplotlib.dates as mdates

from pandas_datareader import data
import numpy as np

from plot import plot
import matplotlib.pyplot as plt

from conf import Configuration
from prices import Prices


prices_manager = None


def load_data(start_date, end_date, symbol):
    global prices_manager

    data = prices_manager.load(symbol)
    all_weekdays = pd.date_range(start=start_date, end=end_date, freq='B')
    data = data.reindex(all_weekdays).ffill()
    return data
    # return data.loc[start_date:end_date]


conf = Configuration('..')
prices_manager = Prices('prices', conf['se'])
se = 'bcba'
range_dates = ('2017-01-01', '2019-09-06')
zoom_dates = ('2019-08-05', range_dates[1])
symbols = conf.symbols()

blacklist = set(['CAPU', 'PESA', 'PSUR', 'POLL'])

print("using dates [%s - %s]" % range_dates)

for symbol in symbols:
    if symbol in blacklist:
        print(symbol, '(blacklisted)')
        continue

    print(symbol)
    data = load_data(range_dates[0], range_dates[1], symbol)
    close = data['Adj Close']

    mas = dict()
    for i in range(2, 200):
        col = 'sma_%d' % i
        mas[col] = close.rolling(i).mean()
        col = 'ema_%d' % i
        mas[col] = close.ewm(span=i, adjust=False).mean()

    ma_short = mas['ema_5']
    ma_med = mas['ema_20']

    signals = None
    # signals = pd.DataFrame(index=ma_short.index)
    # signals = signals[np.where(ma_short > ma_med, 1, -1)]
    # signals = signals.diff()
    signals = ma_short - ma_med
    signals[signals > 0] = 1
    signals[signals < 0] = -1
    signals = signals.diff()
    signals[signals > 0] = 1
    signals[signals < 0] = -1

    action = signals[range_dates[1]]
    if action != 0:
        msg = "sell" if action < 0 else "buy"
        print("\tsignal:", msg)

    fig = plot(range_dates, zoom_dates, symbol, data,
               (
                    (close, 'Price'),
                    (ma_short, 'EMA 5'),
                    (ma_med, 'EMA 20'),
               ), signals)

    plt.savefig('charts/' + symbol + '.png')
    # plt.show()
    plt.close(fig)
