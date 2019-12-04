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
    BASE_FNAME = 'base'

    def __init__(self, data_path):
        self.data_path = data_path

    def load_base(self):
        return self.load(CheckpointManager.BASE_FNAME)

    def save_base(self, data):
        return self.save(CheckpointManager.BASE_FNAME, data)

    def load(self, fname):
        path = self._get_fname_for(fname)
        if not os.path.exists(path):
            return None

        with open(path, 'rb') as file:
            return pickle.load(file)

    def save(self, fname, data):
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)

        with open(self._get_fname_for(fname), 'wb') as file:
            pickle.dump(data, file)

    def _get_fname_for(self, fname):
        return os.path.join(self.data_path, fname + '.pickle')


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


class StrategyFinderMA:
    CKP_FNAME = 'all_ma_returns'

    def __init__(self, ckp_manager):
        self.ckp_manager = ckp_manager

    def load(self, symbols):
        data = self.ckp_manager.load(StrategyFinderMA.CKP_FNAME)
        if data is None:
            self.last_symbol = None
            self.days_range = (5, 20)#300)
            self.min_days = 4
            self.returns = ReturnsManager(symbols, self.days_range, self.min_days)
        else:
            self.returns = data['returns']
            self.last_symbol = data['last_symbol']
            self.days_range = data['days_range']
            self.min_days = data['min_days']

    def save(self):
        data = {
            'last_symbol': self.last_symbol,
            'returns': self.returns,
            'days_range': self.days_range,
            'min_days': self.min_days,
        }
        self.ckp_manager.save(
            StrategyFinderMA.CKP_FNAME,
            data)


conf = Configuration('..')

ckp_manager = CheckpointManager('checkpoint')
strategy = StrategyFinderMA(ckp_manager)

data = ckp_manager.load_base()
if data is not None:
    print('last checkpoint loaded')
    symbols = data['symbols']
    all_data = data['all_data']
else:
    prices_manager = Prices('prices', conf['se'])
    today = date.today()
    range_dates = ('2017-01-01', today.isoformat())
    blacklist = set(['CAPU', 'PESA', 'PSUR', 'POLL'])
    symbols = conf.symbols()
    all_data = load_all_data(prices_manager, blacklist, symbols, range_dates)
    print("using dates [%s - %s]" % range_dates)

    state = {
        'all_data': all_data,
        'symbols': symbols,
    }
    ckp_manager.save_base(state)

strategy.load(all_data.keys())


from timeit import default_timer as timer

print()
last_symbol = strategy.last_symbol
for symbol, data in all_data.items():
    if last_symbol is not None:
        if last_symbol == symbol:
            last_symbol = None
        continue

    price = data['Adj Close']

    signals = pd.DataFrame(index=price.index)
    for i in range(strategy.days_range[0], strategy.days_range[1] + 1):
        col = 'sma_%d' % i
        signals[col] = price.rolling(i).mean()
        col = 'ema_%d' % i
        signals[col] = price.ewm(span=i, adjust=False).mean()

    signals['price'] = price
    positions = pd.DataFrame(index=signals.index).fillna(0)
    for i in range(strategy.days_range[0], strategy.days_range[1] + 1):
        progress = (i / (strategy.days_range[1] - strategy.days_range[0])) * 100
        print(f"\r{symbol} {progress:2.0f}%", end='', flush=True)

        run_times = {
            'signal': 0,
            'returns': 0,
        }
        for j in range(i + strategy.min_days, strategy.days_range[1] + 1):
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

            strategy.returns.set_return(symbol, short_window, long_window, total_return)
            # print(f'ma: [{short_window}, {long_window}], value: ${value:.2f}, total returns: {total_return:.2f}%')

        # print(f' times: {run_times} (in secs)')
    print(f"\r{symbol}", strategy.returns.max_for(symbol))
    strategy.last_symbol = symbol
    strategy.save()

print(strategy.returns)
