import pandas as pd
import matplotlib.dates as mdates

from pandas_datareader import data
import numpy as np

from plot import plot
import matplotlib.pyplot as plt

from conf import Configuration
from prices import Prices
from datetime import date, timedelta


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
today = date.today()
range_dates = ('2017-01-01', today.isoformat())
zoom_dates = (
    (today - timedelta(days=40)).isoformat(),
    today)
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

    if close.isnull().all():
        print("\t is empty")
        continue

    signals = pd.DataFrame(index=data.index)
    for i in range(2, 200):
        col = 'sma_%d' % i
        signals[col] = close.rolling(i).mean()
        col = 'ema_%d' % i
        signals[col] = close.ewm(span=i, adjust=False).mean()

    short_window = 5
    long_window = 20
    ma_short = signals['ema_%d' % short_window]
    ma_long = signals['ema_%d' % long_window]

    signals['signal'] = 0
    signals['signal'][short_window:] = np.where(
                                            ma_short[short_window:] > ma_long[short_window:], 1, 0)
    signals['position'] = signals['signal'].diff()

    action = signals['position'][range_dates[1]]
    if action != 0:
        msg = "sell" if action < 0 else "buy"
        print("\tsignal:", msg)

    fig = plot(range_dates, zoom_dates, symbol, data,
               (
                    (close, 'Price'),
                    (ma_short, 'EMA %d' % short_window),
                    (ma_long, 'EMA %d' % long_window),
               ), signals)

    plt.savefig('charts/' + symbol + '.png')
    # plt.show()
    plt.close(fig)
