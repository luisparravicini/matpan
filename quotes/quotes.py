import requests
import time
from bs4 import BeautifulSoup
import cache
import re
import yaml


def get_url(url):
    print('fetching', url)
    response = requests.get(url)
    status = response.status_code
    if status != 200:
        print('Unexpected response status: ' + status)
        sys.exit(1)
    return response

#def get_url(url):
#


if __name__ == '__main__':
    conf = None
    with open('../conf.yaml', 'r') as file:
        conf = yaml.safe_load(file.read())

    url = conf['url']
    cache.setup('cache')
    data = cache.try_get(url)
    if data is None:
        response = get_url(url)
        data = response.text
        cache.save(url, data)

    soup = BeautifulSoup(data, 'html.parser')
    for link in soup.findAll('a'):
        name = link['href']
        match = re.fullmatch(conf['id_re'], name)
        if match is not None:
            id = match.group(1)
            symbol = link.text.strip().encode().hex()
            name = link['title']
            print(id, symbol, name)
            print('-----')
