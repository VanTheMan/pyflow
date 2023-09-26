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

Another problem here is that when you call a function, there is no autocomplete for the arguments.
So you have to know what the arguments are before you call the function. This is not very user friendly.
"""


class Pyflow:
    path = f"{Path.home()}/.pyflow"

    def __init__(self):
        pass

    def load_functions(self):
        if not os.path.exists(f"{self.path}/functions"):
            os.makedirs(f"{self.path}/functions")

        # TODO: add typing and doc strings
        function_module = "class PyflowFn:\n"
        function_module += "    def __init__(self, pf):\n"
        function_module += "        self.pf = pf\n\n"

        for func in os.listdir(f"{self.path}/functions"):
            metadata = json.loads(open(f"{self.path}/functions/{func}", "r").read())
            variables = metadata["variables"]

            function_module += f"    def {func}({', '.join(['self'] + variables)}):\n"
            function_module += f"        return self.pf.function('{func}')({', '.join(variables)})\n\n"
        open("pyflow_functions.py", "w").write(function_module)

    def register(self, func):
        print(f"Registering variables: {func.__code__.co_varnames}")
        metadata = {
            "variables": func.__code__.co_varnames,
            "pickle": codecs.encode(cloudpickle.dumps(func), "base64").decode(),
        }

        open(f"{self.path}/functions/{func.__name__}", "w").write(json.dumps(metadata))

    def function(self, func_name):
        metadata = json.loads(open(f"{self.path}/functions/{func_name}", "r").read())
        func = cloudpickle.loads(codecs.decode(metadata["pickle"].encode(), "base64"))
        return func

    def register_module(self, module):
        cloudpickle.register_pickle_by_value(module)
