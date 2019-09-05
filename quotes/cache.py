import os
# import shutil
import hashlib


_cache_path = None


def setup(path):
    global _cache_path
    _cache_path = path
    # if os.path.exists(path):
    #     shutil.rmtree(path)
    if not os.path.isdir(path):
        os.mkdir(path)


def save(url, data):
    path = _to_fname(url)
    with open(path, 'w') as file:
        file.write(data)


def try_get(url):
    path = _to_fname(url)
    data = None
    if os.path.isfile(path):
        with open(path, 'r') as file:
            data = file.read()
    return data


def _to_fname(url):
    global _cache_path
    digest = hashlib.sha256(url.encode('utf-8')).hexdigest()
    return os.path.join(_cache_path, digest)
