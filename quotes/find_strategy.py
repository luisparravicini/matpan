import pandas as pd

from pandas_datareader import data
import numpy as np

from plot import plot

from conf import Configuration
from prices import Prices
from datetime import date, timedelta
from loader import load_all_data

import os
import pickle


class CheckpointManager:
    def __init__(self, data_path):
        self.data_path = data_path

    def load(self):
        if not self.has_checkpoint():
            return None

        with open(self.data_path, 'rb') as file:
            return pickle.load(file)

    def has_checkpoint(self):
        return os.path.exists(self.data_path)

    def save(self, data):
        with open(self.data_path, 'wb') as file:
            pickle.dump(data, file)



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



conf = Configuration('..')

ckp_manager = CheckpointManager('checkpoint.pickle')

if ckp_manager.has_checkpoint():
    print('loading last checkpoint')
    data = ckp_manager.load()
    symbols = data['symbols']
    all_data = data['all_data']
    last_symbol = data['last_symbol']
    days_range = data['days_range']
    min_days = data['min_days']
    returns = data['returns']
else:
    prices_manager = Prices('prices', conf['se'])
    today = date.today()
    range_dates = ('2017-01-01', today.isoformat())
    blacklist = set(['CAPU', 'PESA', 'PSUR', 'POLL'])
    symbols = conf.symbols()
    all_data = load_all_data(prices_manager, blacklist, symbols, range_dates)
    print("using dates [%s - %s]" % range_dates)
    last_symbol = None
    days_range = (5, 300)
    min_days = 4
    returns = ReturnsManager(all_data.keys(), days_range, min_days)


from timeit import default_timer as timer

print()
for symbol, data in all_data.items():
    if last_symbol is not None:
        if last_symbol == symbol:
            last_symbol = None
        continue

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

        run_times = {
            'signal': 0,
            'returns': 0,
        }
        for j in range(i + min_days, days_range[1] + 1):
            short_window = i
            long_window = j
            ma_short = signals['ema_%d' % short_window]
            ma_long = signals['ema_%d' % long_window]

            start = timer()
            signals['signal'] = np.where(ma_short > ma_long, 1, 0)
            signals.loc[:short_window, 'signal'] = 0

            signals['position'] = signals['signal'].diff()
            end = timer()
            run_times['signal'] += end - start

            # should you buy/sell today?
            # action = signals['position'][range_dates[1]]
            # if action != 0:
            #     msg = "sell" if action < 0 else "buy"
            #     print("\tsignal:", msg)


            start = timer()
            initial_capital = 1000000
            shares = 1000
            print(signals['signal'].count)
            positions['position'] = shares * signals['signal']
            portfolio = positions.multiply(price, axis=0)

            pos_diff = portfolio.diff()

            portfolio['holdings'] = (positions.multiply(price, axis=0)).sum(axis=1)
            portfolio['cash'] = initial_capital - (pos_diff.multiply(price, axis=0)).sum(axis=1).cumsum()
            portfolio['total'] = portfolio['cash'] + portfolio['holdings']
            portfolio['returns'] = portfolio['total'].pct_change()

            # print(portfolio.tail())
            value = portfolio['total'].tail(1).values[0]
            total_return = ((value / initial_capital) - 1) * 100
            # print(f'value: ${value:.2f}, total returns: {total_return:.2f}%')
            end = timer()
            run_times['returns'] += end - start

            returns.set_return(symbol, short_window, long_window, total_return)
            # print(f'ma: [{short_window}, {long_window}], value: ${value:.2f}, total returns: {total_return:.2f}%')

        # print(f' times: {run_times} (in secs)')
    print(f"\r{symbol}", returns.max_for(symbol))
    state = {
        'all_data': all_data,
        'last_symbol': symbol,
        'symbols': symbols,
        'days_range': days_range,
        'min_days': min_days,
        'returns': returns,
    }
    ckp_manager.save(state)

print(returns)
