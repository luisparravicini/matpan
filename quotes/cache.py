import os
# import shutil
import hashlib
import json


class Cache:

    GET_METHOD = 'get'
    POST_METHOD = 'post'

    def __init__(self, path):
        self._cache_path = path
        # if os.path.exists(path):
        #     shutil.rmtree(path)
        if not os.path.isdir(path):
            os.mkdir(path)

    def save(self, method, url, data, params=None):
        path = self._to_fname(method, url, params)
        with open(path, 'w') as file:
            file.write(data)

    def try_get(self, method, url, params=None):
        path = self._to_fname(method, url, params)
        data = None
        if os.path.isfile(path):
            with open(path, 'r') as file:
                data = file.read()
        return data

    def _to_fname(self, method, url, params):
        global _cache_path
        s = json.dumps([method, url, params])
        digest = hashlib.sha256(s.encode('utf-8')).hexdigest()
        return os.path.join(self._cache_path, digest)
