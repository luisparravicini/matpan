import pandas as pd
import matplotlib.dates as mdates

from pandas_datareader import data
import numpy as np

from plot import plot

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

create_plot = False

if create_plot:
    import matplotlib.pyplot as plt

all_data = load_all_data(blacklist)

class ReturnsManager:
    def __init__(self, symbols, days_range, min_days):
        print()

        self.symbols = list(symbols)
        self.columns = dict()
        self.columns_indices = list()
        index = 0
        for i in range(days_range[0], days_range[1] + 1):
            for j in range(i + min_days, days_range[1] + 1):
                col = 'ema_%d-ema_%d' % (i, j)
                self.columns[col] = index
                self.columns_indices.append(col)
                index += 1
        self.data = np.empty((len(symbols), len(self.columns)), dtype=np.float16)
        self.data.fill(np.nan)

    def set_return(self, symbol, days_a, days_b, value):
        col_name = 'ema_%d-ema_%d' % (days_a, days_b)
        col = self.columns[col_name]
        row = self.symbols.index(symbol)
        self.data[row][col] = total_return

    def max_for(self, symbol):
        row = self.symbols.index(symbol)
        row_data = self.data[row]
        max_value = np.amax(row_data)
        max_indices = np.where(row_data == max_value)[0]
        values = list()
        for m in max_indices:
            datum = (m, self.columns_indices[m], max_value)
            values.append(datum)
        return values


print()
days_range = (5, 90)#200)
min_days = 4
returns = ReturnsManager(all_data.keys(), days_range, min_days)
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
    for i in range(days_range[0], days_range[1] + 1):
        progress = (i / (days_range[1] - days_range[0])) * 100
        print(f"\r{symbol} {progress:2.0f}%", end='', flush=True)

        for j in range(i + min_days, days_range[1] + 1):
            short_window = i
            long_window = j
            ma_short = signals['ema_%d' % short_window]
            ma_long = signals['ema_%d' % long_window]

            signals['signal'] = 0
            signals['signal'][short_window:] = np.where(
                                                    ma_short[short_window:] > ma_long[short_window:], 1, 0)
            signals['position'] = signals['signal'].diff()

            # should you buy/sell today?
            # action = signals['position'][range_dates[1]]
            # if action != 0:
            #     msg = "sell" if action < 0 else "buy"
            #     print("\tsignal:", msg)


            initial_capital = 1000000
            shares = 1000
            positions['position'] = shares * signals['signal']
            portfolio = positions.multiply(price, axis=0)

            pos_diff = portfolio.diff();

            portfolio['holdings'] = (positions.multiply(price, axis=0)).sum(axis=1)
            portfolio['cash'] = initial_capital - (pos_diff.multiply(price, axis=0)).sum(axis=1).cumsum()
            portfolio['total'] = portfolio['cash'] + portfolio['holdings']
            portfolio['returns'] = portfolio['total'].pct_change()

            del portfolio['position']
            
            # print(portfolio.tail())
            value = portfolio['total'].tail(1).values[0]
            total_return = ((value / initial_capital) - 1) * 100
            # print(f'value: ${value:.2f}, total returns: {total_return:.2f}%')

            returns.set_return(symbol, short_window, long_window, total_return)
            # print(f'ma: [{short_window}, {long_window}], value: ${value:.2f}, total returns: {total_return:.2f}%')

    print(f"\r{symbol}", returns.max_for(symbol))

    if create_plot:
        fig = plot(range_dates, zoom_dates, symbol, data,
                   (
                        (price, 'Price'),
                        (ma_short, 'EMA %d' % short_window),
                        (ma_long, 'EMA %d' % long_window),
                   ), signals)

        plt.savefig('charts/' + symbol + '.png')
        # plt.show()
        plt.close(fig)

print(returns)
