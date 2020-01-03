from datetime import date, timedelta
from prices import Prices
from conf import Configuration
from loader import load_all_data
from checkpoint_manager import CheckpointManager
import pandas as pd
import numpy as np
from strategies import StrategyFindBestMA, StrategyRandom01


def setup():
    conf = Configuration('..')
    prices_manager = Prices('prices', conf['se'])
    today = date.today()
    range_dates = ('2017-01-01', today.isoformat())

    ckp_manager = CheckpointManager('checkpoint')
    data = ckp_manager.load_base()

    if data is not None:
        print('last checkpoint loaded')
        symbols = data['symbols']
        all_data = data['all_data']
    else:
        blacklist = set(['CAPU', 'PESA', 'PSUR', 'POLL'])
        symbols = conf.symbols()
        all_data = load_all_data(prices_manager, blacklist, symbols, range_dates)

        print('calculating returns')
        for data in all_data.values():
            # TODO there must be a better way to do this
            returns = pd.DataFrame(data['Adj Close']).apply(
                lambda x:
                np.log(x) - np.log(x.shift()))
            data['Daily Return'] = returns

        state = {
            'all_data': all_data,
            'symbols': symbols,
        }

        ckp_manager.save_base(state)

    print("using dates [%s - %s]" % range_dates)

    # strategy = StrategyFindBestMA(ckp_manager)
    strategy = StrategyRandom01(ckp_manager)
    print(f'using strategy {type(strategy).__name__}')
    strategy.load(all_data.keys(), all_data)

    return (
        today,
        range_dates,
        conf,
        prices_manager,
        all_data,
        ckp_manager,
        strategy)
