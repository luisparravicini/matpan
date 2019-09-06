import requests
import time
from bs4 import BeautifulSoup
from cache import Cache
import re
import yaml
from random import shuffle
from datetime import datetime


conf = None


def get_url(url):
    print(f'fetching {url}')
    response = requests.get(url)
    status = response.status_code
    if status != 200:
        print(f'Unexpected response status: {status}')
        sys.exit(1)
    return response


def post_url(url, req_data):
    print(f'fetching {url} with {req_data}')
    response = requests.post(url, data=req_data)
    status = response.status_code
    if status != 200:
        print(f'Unexpected response status: {status}')
        sys.exit(1)
    return response


def _read_conf():
    global conf
    with open('../conf.yaml', 'r') as file:
        conf = yaml.safe_load(file.read())


def _save_conf():
    global conf
    with open('../conf.yaml', 'w') as file:
        yaml.safe_dump(conf, file)


def _get_fetch(url):
    data = cache.try_get(Cache.GET_METHOD, url)
    if data is None:
        response = get_url(url)
        data = response.text
        cache.save(url, Cache.GET_METHOD, data)
    return data


def _setup_symbols():
    global conf
    symbols_key = 'symbols'

    if symbols_key in conf:
        return

    symbols_url = conf['symbols_url']
    data = _get_fetch(symbols_url)
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


def _update_prices():
    global conf

    symbols = conf['symbols'].copy()
    # shuffle(symbols)
    for datum in symbols:
        id, symbol, _ = datum
        print(symbol)

        start_date = datetime.strptime('2018-01-01', '%Y-%m-%d')
        end_date = datetime.strptime('2019-09-01', '%Y-%m-%d')

        date_range = " - ".join([
            start_date.strftime('%d/%m/%Y'),
            end_date.strftime('%d/%m/%Y'),
        ])
        req_data = dict()
        params = conf['price_params']
        req_data[params['dates']] = date_range
        req_data[params['id']] = id
        req_data = {**req_data, **params['extras']}

        price_url = conf['price_url']
        data = cache.try_get(Cache.POST_METHOD, price_url, req_data)
        if data is None:
            response = post_url(price_url, req_data)
            data = response.text
            cache.save(Cache.POST_METHOD, price_url, data, params=req_data)

        # print(data)



if __name__ == '__main__':
    cache = Cache('cache')
    _read_conf()
    _setup_symbols()
    _update_prices()
