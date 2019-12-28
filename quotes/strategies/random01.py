import pandas as pd
import numpy as np
from .returns_finder import ReturnsFinder


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
        self.data = np.empty(
            (len(symbols), len(self.columns)),
            dtype=np.float16)
        self.data.fill(np.nan)

    def set_return(self, symbol, days_a, days_b, value):
        col_name = 'ema_%d-ema_%d' % (days_a, days_b)
        col = self.columns[col_name]
        row = self.symbols.index(symbol)
        self.data[row][col] = value

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


class StrategyRandom01:
    CKP_FNAME = 'all_ma_returns'

    def __init__(self, ckp_manager):
        self.ckp_manager = ckp_manager

    def run(self):
        for symbol, data in self.all_data.items():
            price = data['Adj Close']
            print(symbol)
            self._process_ma(symbol, price)

    def _process_ma(self, symbol, price):
        signals = pd.DataFrame(index=price.index)

        signals['price'] = price
        signals['signal'] = 0
        returns = ReturnsFinder(signals)

        total = self.days_to_hold + self.days_to_rest
        d = 0
        for j in range(0, len(signals)):
            if d < self.days_to_hold:
                signals['signal'].iloc[j] = 1
            else:
                signals['signal'].iloc[j] = 0

            d += 1
            if d >= total:
                d = 0

        value, total_return = returns.update(signals)
        print(f'${value} / {total_return}%')

        # self.returns.set_return(symbol, short_window, long_window, total_return)
        # print(f'ma: [{short_window}, {long_window}], value: ${value:.2f}, total returns: {total_return:.2f}%')

        # print(f"\r{symbol}", self.returns.max_for(symbol))
        self.save()

    def load(self, symbols, all_data):
        self.all_data = all_data
        # data = self.ckp_manager.load(StrategyFindBestMA.CKP_FNAME)
        # if data is None:
        self.days_range = (5, 300)
        self.days_to_hold = 10
        self.days_to_rest = 5
        #     self.returns = ReturnsManager(symbols, self.days_range, self.min_days)
        self.returns = dict()
        # else:
        #     self.returns = data['returns']
        #     self.days_range = data['days_range']
        #     self.min_days = data['min_days']

    def save(self):
        pass
        # data = {
        #     'returns': self.returns,
        #     'days_range': self.days_range,
        #     'min_days': self.min_days,
        # }
        # self.ckp_manager.save(
        #     StrategyFindBestMA.CKP_FNAME,
        #     data)
