import time
from bs4 import BeautifulSoup
import re
import yaml
from random import shuffle
from datetime import datetime, date, timedelta
from downloader import Downloader
import os
import pandas as pd


conf = None
downloader = None
prices_manager = None


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

def _read_conf():
    global conf
    with open('../conf.yaml', 'r') as file:
        conf = yaml.safe_load(file.read())


def _save_conf():
    global conf
    with open('../conf.yaml', 'w') as file:
        yaml.safe_dump(conf, file)


def _setup_symbols():
    global conf
    global downloader
    symbols_key = 'symbols'

    if symbols_key in conf:
        return

    symbols_url = conf['symbols_url']
    data = downloader.get(symbols_url)
    symbols = list()
    soup = BeautifulSoup(data, 'html.parser')
    for link in soup.findAll('a'):
        name = link['href']
        match = re.fullmatch(conf['id_re'], name)
        if match is not None:
            id = match.group(1)
            symbol = link.text.strip()
            symbol = symbol.split("\n")[0].strip()
            name = link['title']
            symbols.append((id, symbol, name))

    conf[symbols_key] = symbols
    print(f'parsed {len(symbols)} symbols')
    _save_conf()


def to_date(s):
    return datetime.strptime(s, '%Y-%m-%d').date()


def to_req_str(d):
    return d.strftime('%d/%m/%Y')


def from_req_str(s):
    return datetime.strptime(s, '%m/%d/%Y').date()


def _update_prices():
    global conf
    global downloader
    global prices_manager

    symbols = conf['symbols'].copy()
    # shuffle(symbols)
    for datum in symbols:
        id, symbol, _ = datum

        print(symbol, end='\t')

        start_date = to_date('2018-01-01')
        end_date = date.today()

        cur_prices = prices_manager.load(symbol)
        if cur_prices is not None:
            if cur_prices.empty:
                print('empty')
                continue

            start_date = cur_prices.index.max().date() + timedelta(days=1)

        if end_date == start_date:
            print()
            continue

        date_range = " - ".join([
            to_req_str(start_date),
            to_req_str(end_date),
        ])
        req_data = dict()
        params = conf['price_params']
        req_data[params['dates']] = date_range
        req_data[params['id']] = id
        req_data = {**req_data, **params['extras']}

        print(f'{start_date.isoformat()} - {end_date.isoformat()}')

        price_url = conf['price_url']
        data = downloader.post(price_url, req_data)

        dates = list()
        prices_data = list()
        soup = BeautifulSoup(data, 'html.parser')
        for row in soup.findAll('tr'):
            if len(row.findAll('th')) == 8:
                continue

            cols = row.findAll('td')
            if len(cols) != 8:
                print('Unpexected number of columns')
                os.sys.exit(1)

            datum = [x.text for x in cols]

            row_date = from_req_str(datum[0])
            dates.append(row_date)

            cols = [float(x.replace(',', '')) for x in datum[1:]]
            prices_data.append(cols)

        prices = pd.DataFrame(data=prices_data,
                              index=dates,
                              columns=[
                                'Open', 'Max', 'Min',
                                'Close', 'Adj Close',
                                'Volume',
                                'Nominal volume'
                              ])
        prices.index.name = 'Date'

        if cur_prices is None:
            cur_prices = prices
        else:
            cur_prices = cur_prices.append(prices, sort=True)

        prices_manager.save(symbol, cur_prices)


if __name__ == '__main__':
    _read_conf()
    downloader = Downloader('cache')
    prices_manager = Prices('prices', conf['se'])
    _setup_symbols()
    _update_prices()
