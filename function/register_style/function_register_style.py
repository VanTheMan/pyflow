import cloudpickle
import json
import os
from pathlib import Path
import codecs

"""
The benefit of this style is that you can register the functions without executing them.
The issue with this is that pickling the function is not very human readable. To establish provenance,
you would need to store the function itself, which is not very human readable.  You could also store
the function name and the arguments that were passed to it, but this is not very robust.  You could
also store the function name and the hash of the function, but this is not very human readable either.
"""


class Pyflow:
    path = f"{Path.home()}/.pyflow"

    def __init__(self):
        self.functions = set(self._load_functions())

    def _load_functions(self):
        if not os.path.exists(f"{self.path}/functions"):
            os.makedirs(f"{self.path}/functions")
        # The editor sadly does not autocomplete these loaded functions
        # [self.__setattr__(func, self.load_function(func)) for func in os.listdir(f"{self.path}/functions")]
        return os.listdir(f"{self.path}/functions")

    def register(self, func):
        print(f"Registering variables: {func.__code__.co_varnames}")
        metadata = {
            "variables": func.__code__.co_varnames,
            "pickle": codecs.encode(cloudpickle.dumps(func), "base64").decode(),
        }

        open(f"{self.path}/functions/{func.__name__}", "w").write(json.dumps(metadata))
        # TODO: Add a check to see if the function is already registered
        self.functions.add(func.__name__)

    def function(self, func_name):
        metadata = json.loads(open(f"{self.path}/functions/{func_name}", "r").read())
        func = cloudpickle.loads(codecs.decode(metadata["pickle"].encode(), "base64"))
        return func

    def register_module(self, module):
        cloudpickle.register_pickle_by_value(module)
