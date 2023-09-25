import cloudpickle
import json
import os
from pathlib import Path
import codecs


class Pyflow:
    path = f"{Path.home()}/.pyflow"

    def __init__(self):
        self.functions = set(self._load_functions())

    def _load_functions(self):
        if not os.path.exists(f"{self.path}/functions"):
            os.makedirs(f"{self.path}/functions")
        return os.listdir(f"{self.path}/functions")

    def register_function(self, func):
        print(f"Registering variables: {func.__code__.co_varnames}")
        metadata = {
            "variables": func.__code__.co_varnames,
            "pickle": codecs.encode(cloudpickle.dumps(func), "base64").decode(),
        }

        open(f"{self.path}/functions/{func.__name__}", "w").write(json.dumps(metadata))
        # TODO: Add a check to see if the function is already registered
        self.functions.add(func.__name__)

    def load_function(self, func_name):
        metadata = json.loads(open(f"{self.path}/functions/{func_name}", "r").read())
        func = cloudpickle.loads(codecs.decode(metadata["pickle"].encode(), "base64"))
        return func


def step1(x: int, y: int):
    print(f"step {x} {y}")
    return 1


def step2(step1_output):
    print(step1_output)
    return 2


pf = Pyflow()

pf.register_function(step1)
pf.register_function(step2)
# You can register a function, class, file, or directory

print(pf.functions)
pf.load_function("step1")(1, 2)
