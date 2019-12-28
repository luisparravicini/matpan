from strategies import StrategyFindBestMA, StrategyRandom01
from setup import setup


_, _, _, _, all_data, ckp_manager = setup()

# strategy = StrategyFindBestMA(ckp_manager)
strategy = StrategyRandom01(ckp_manager)

strategy.load(all_data.keys(), all_data)
strategy.run()

print(strategy.returns)
