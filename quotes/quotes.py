import requests
import time
from bs4 import BeautifulSoup
from cache import Cache
import re
import yaml


conf = None


def get_url(url):
    print('fetching', url)
    response = requests.get(url)
    status = response.status_code
    if status != 200:
        print('Unexpected response status: ' + status)
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


def _setup_symbols():
    global conf
    symbols_key = 'symbols'

    if symbols_key in conf:
        return

    symbols_url = conf['symbols_url']
    data = cache.try_get(symbols_url)
    if data is None:
        response = get_url(url)
        data = response.text
        cache.save(url, data)

    symbols = list()
    soup = BeautifulSoup(data, 'html.parser')
    for link in soup.findAll('a'):
        name = link['href']
        match = re.fullmatch(conf['id_re'], name)
        if match is not None:
            id = match.group(1)
            symbol = link.text.strip()
            symbol = symbol.split("\n")[0]
            name = link['title']
            symbols.append((id, symbol, name))

    conf[symbols_key] = symbols
    print('parsed', len(symbols), 'symbols')
    _save_conf()


if __name__ == '__main__':
    cache = Cache('cache')
    _read_conf()
    _setup_symbols()
