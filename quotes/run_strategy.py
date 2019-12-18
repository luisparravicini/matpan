import pandas as pd

from pandas_datareader import data
import numpy as np

from plot import plot

from conf import Configuration
from prices import Prices
from datetime import date, timedelta
from loader import load_all_data

import os
from checkpoint_manager import CheckpointManager
from strategies import StrategyFindBestMA, StrategyRandom01


conf = Configuration('..')

ckp_manager = CheckpointManager('checkpoint')
# strategy = StrategyFindBestMA(ckp_manager)
strategy = StrategyRandom01(ckp_manager)

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

strategy.load(all_data.keys(), all_data)
strategy.run()

print(strategy.returns)
