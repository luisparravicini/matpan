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

def load_all_data(blacklist):
    print('loading quotes')

    all_data = dict()
    for symbol in symbols:
        if symbol in blacklist:
            print(symbol, '(blacklisted)')
            continue

        data = load_data(range_dates[0], range_dates[1], symbol)
        close = data['Adj Close']

        if close.isnull().all():
            print(symbol, '(empty)')
            continue

        all_data[symbol] = data
        print(symbol, end="\r")

    return all_data


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

all_data = load_all_data(blacklist)

print()
days_range = (5, 90)#200)
min_days = 4
for symbol, data in all_data.items():
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
                                            ma_short[short_window:] > ma_long[short_window:], 1, 0)
    signals['position'] = signals['signal'].diff()

    fig = plot(range_dates, zoom_dates, symbol, data,
               (
                    (price, 'Price'),
                    (ma_short, 'EMA %d' % short_window),
                    (ma_long, 'EMA %d' % long_window),
               ), signals)

    plt.savefig('charts/' + symbol + '.png')
    # plt.show()
    plt.close(fig)
