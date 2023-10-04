import pickle


class PyflowStorageObject:
    def __init__(self, path):
        self.path = path

    def load(self):
        return pickle.load(open(self.path, "rb"))

    def dump(self, arg):
        pickle.dump(arg, open(self.path, "wb"))
