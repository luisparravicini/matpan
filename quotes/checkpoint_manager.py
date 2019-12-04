import os
import pickle


class CheckpointManager:
    BASE_FNAME = 'base'

    def __init__(self, data_path):
        self.data_path = data_path

    def load_base(self):
        return self.load(CheckpointManager.BASE_FNAME)

    def save_base(self, data):
        return self.save(CheckpointManager.BASE_FNAME, data)

    def load(self, fname):
        path = self._get_fname_for(fname)
        if not os.path.exists(path):
            return None

        with open(path, 'rb') as file:
            return pickle.load(file)

    def save(self, fname, data):
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)

        with open(self._get_fname_for(fname), 'wb') as file:
            pickle.dump(data, file)

    def _get_fname_for(self, fname):
        return os.path.join(self.data_path, fname + '.pickle')
