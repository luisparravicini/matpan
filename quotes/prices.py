import os
import pandas as pd

class Prices:
    EXT = '.csv'

    def __init__(self, base_dir, se):
        self.se = se
        self.prices_path = os.path.join(base_dir, se)
        os.makedirs(self.prices_path, exist_ok=True)

    def save(self, symbol, data):
        path = os.path.join(self.prices_path, symbol + Prices.EXT)
        data.to_csv(path, index_label='Date')

    def load(self, symbol):
        path = os.path.join(self.prices_path, symbol + Prices.EXT)
        if os.path.exists(path):
            return pd.read_csv(path,
                               parse_dates=True,
                               index_col='Date')
        return None
