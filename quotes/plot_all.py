import pandas as pd
from datetime import timedelta
from setup import setup
import numpy as np
from plot import plot
import matplotlib.pyplot as plt
from loader import load_index_data
import argparse


parser = argparse.ArgumentParser(description='Plot quotes')
parser.add_argument('--symbol', help='plot only SYMBOL')
args = parser.parse_args()


today, range_dates, conf, prices_manager, all_data, _, strategy = setup()
zoom_dates = (
    (today - timedelta(days=40)).isoformat(),
    today)

index_symbol = conf.index_symbol()
index_data = load_index_data(prices_manager, index_symbol, range_dates)
index_close = index_data[index_symbol]['Adj Close']
# TODO: plot index

print()
days_range = (20, 90)  # 200)
min_days = 4

if args.symbol is None:
    symbols = all_data.keys()
else:
    symbols = [args.symbol]

for symbol in symbols:
    data = all_data[symbol]
    price = data['Adj Close']

    signals, strategy_plot_series = strategy.signals(symbol, days_range)
    plot_series = ((price, 'Price'),) + strategy_plot_series
    fig = plot(range_dates, zoom_dates, symbol,
               data, plot_series, signals)

    plt.savefig('charts/' + symbol + '.png')
    # plt.show()
    plt.close(fig)
