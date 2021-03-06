import time
from bs4 import BeautifulSoup
import re
from random import shuffle
from datetime import datetime, date, timedelta
from downloader import Downloader
import os
import pandas as pd
from prices import Prices
from conf import Configuration
import json

conf = None
downloader = None
prices_manager = None


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


def to_req_str(d):
    return d.strftime('%d/%m/%Y')


def to_index_req_str(d):
    return d.strftime('%d-%m-%Y')


def from_req_str(s):
    return datetime.strptime(s, '%m/%d/%Y').date()


def from_index_req_str(s):
    return datetime.strptime(s, '%d-%m-%Y').date()


def _update_prices():
    global conf
    global downloader
    global prices_manager

    symbols = conf.index() + conf['symbols']
    shuffle(symbols)
    for datum in symbols:
        id, symbol, _ = datum

        print(symbol, end='\t')

        start_date = conf.start_date()
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

        print(f'{start_date.isoformat()} - {end_date.isoformat()}')

        if symbol == conf.index_symbol():
            price_url = conf['index_url']
            price_url = os.path.join(
                            price_url,
                            to_index_req_str(start_date),
                            to_index_req_str(end_date))
            data = json.loads(downloader.get(price_url))
            if len(data) < 2:
                print('Unpexected number of rows')
                os.sys.exit(1)
            cols = data[0]
            expected_cols = ["Fecha", "Apertura", "Ultimo",
                             "Var %", "Max.", "Min."]
            if cols != expected_cols:
                print('Unpexected columns')
                os.sys.exit(1)
            dates = list()
            prices_data = list()
            for row in data[1:]:
                row_date = from_index_req_str(row[0])
                dates.append(row_date)

                row_data = [float(x.replace('.', '').replace(',', '.')) for x in row[1:]]
                datum = [row_data[0], row_data[3], row_data[4], None, row_data[1], None, None]
                prices_data.append(datum)
        else:
            date_range = " - ".join([
                to_req_str(start_date),
                to_req_str(end_date),
            ])
            req_data = dict()
            params = conf['price_params']
            req_data[params['dates']] = date_range
            req_data[params['id']] = id
            req_data = {**req_data, **params['extras']}

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

        prices = pd.DataFrame(
            data=prices_data,
            index=dates,
            columns=[
                'Open', 'Max', 'Min',
                'Close', 'Adj Close',
                'Volumen monto',
                'Volumen nominal'])
        prices.index.name = 'Date'

        if cur_prices is None:
            cur_prices = prices
        else:
            cur_prices = cur_prices.append(prices, sort=True)
            cur_prices.drop_duplicates(keep='last', inplace=True)

        prices_manager.save(symbol, cur_prices)


if __name__ == '__main__':
    conf = Configuration('..')
    downloader = Downloader('cache')
    prices_manager = Prices('prices', conf['se'])
    _setup_symbols()
    _update_prices()
