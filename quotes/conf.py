import yaml
import os


class Configuration:
    def __init__(self, path):
        self.path = os.path.join(path, 'conf.yaml')
        self._load()

    def __getitem__(self, key):
        return self.conf[key]

    def __setitem__(self, key, value):
        self.conf[key] = value

    def __contains__(self, item):
        return item in self.conf

    def symbols(self):
        return [x[1] for x in self['symbols']]

    def _load(self):
        with open(self.path, 'r') as file:
            self.conf = yaml.safe_load(file.read())

    def _save(self):
        with open(self.path, 'w') as file:
            yaml.safe_dump(self.conf, file)
