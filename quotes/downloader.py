import requests
import os
from cache import Cache


class Downloader:

    def __init__(self, cache_dir):
        self.cache = Cache(cache_dir)

    def get(self, url):
        data = self.cache.try_get(Cache.GET_METHOD, url)
        if data is None:
            response = self._do_get(url)
            data = response.text
            self.cache.save(Cache.GET_METHOD, url, data)
        return data

    def post(self, url, req_data):
        data = self.cache.try_get(Cache.POST_METHOD, url, req_data)
        if data is None:
            response = self._do_post(url, req_data)
            data = response.text
            self.cache.save(Cache.POST_METHOD, url, data, params=req_data)
        return data

    def _do_get(self, url):
        print(f'fetching {url}')
        response = requests.get(url)
        self._check_is_ok(response)
        return response

    def _do_post(self, url, req_data):
        # print(f'fetching {url} with {req_data}')
        response = requests.post(url, data=req_data)
        self._check_is_ok(response)
        return response

    def _check_is_ok(self, response):
        status = response.status_code
        if status != 200:
            print(f'Unexpected response status: {status}')
            os.sys.exit(1)
