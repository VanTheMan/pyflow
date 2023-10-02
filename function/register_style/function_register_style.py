import copy

import cloudpickle
import json
import os
from pathlib import Path
import codecs
import inspect
import hashlib
from utils import RunTime, Container, Resources

"""
The benefit of this style is that you can register the functions without executing them.
The issue with this is that pickling the function is not very human readable. To establish provenance,
you would need to store the function itself, which is not very human readable.  You could also store
the function name and the arguments that were passed to it, but this is not very robust.  You could
also store the function name and the hash of the function, but this is not very human readable either.

Another problem here is that when you call a function, there is no autocomplete for the arguments.
So you have to know what the arguments are before you call the function. This is not very user friendly.

Another problem with he pickle approach is that you don't knw the output format. Making it hard to pass
variables along.  You could store the output format in the metadata, but this is not very robust.

Another problem is that not all code can be pickled. You might run into an issue where you cannot use it.
"""


class Pyflow:
    path = f"{Path.home()}/.pyflow"

    def __init__(self):
        pass

    def load_functions(self, annotate=False, path="pyflow_functions.py"):
        """
        This function will load all the functions in the functions directory and create a module.
        This module will have a class called PyflowFn. This class will have a function for each
        function in the functions directory. Note that it is possible for this file to get
        out of sync with the functions directory. So it is the user's reposibility to make sure
        that the functions directory and the module are in sync.

        :param annotate: Should the function be annotated with the type hints? If they are included,
            you will have to import the modules used in the annotations yourself.
        :param path: Where should the module be saved?
        :return:
        """
        if not os.path.exists(f"{self.path}/functions"):
            os.makedirs(f"{self.path}/functions")

        function_module = "class PyflowFn:\n"
        function_module += "    def __init__(self, pf):\n"
        function_module += "        self.pf = pf\n\n"

        for func in os.listdir(f"{self.path}/functions"):
            metadata = json.loads(open(f"{self.path}/functions/{func}", "r").read())
            variables = metadata["variables"]
            outer_vars = copy.deepcopy(variables)
            signature = metadata["signature"]
            is_kwarg = metadata["is_kwarg"]

            if annotate:
                signature = "(self, " + signature[1::]
                # Signature includes the type annotations. This means that you will have to import
                # the modules used in the annotations. The environment you are working in won't
                # necessarily have those packages installed.
                function_module += f"    def {func}{signature}:\n"
            else:
                # All keyword args with default values are set to None. This is because you cannot
                # guarantee that the default type will be available in the environment you are in.
                for i, k in enumerate(is_kwarg):
                    if k:
                        variables[i] += "=None"
                        outer_vars[i] += f"={outer_vars[i]}"
                    if variables[i] == "args":
                        outer_vars[i] = variables[i] = "*args"
                    if variables[i] == "kwargs":
                        outer_vars[i] = variables[i] = "**kwargs"
                function_module += f"    def {func}({', '.join(['self'] + variables)}):\n"
                function_module += f"        \"\"\"{func}{signature}\"\"\"\n"

            function_module += f"        return self.pf.fn('{func}')({', '.join(outer_vars)})\n\n"
        open(path, "w").write(function_module)

    @staticmethod
    def build_conda_yml(runtime: RunTime, path="environment.yml"):
        env = "name: env\n"
        env += "dependencies:\n"
        env += f"  - python={runtime.python_version.value}\n"
        for dep in runtime.conda_dependencies:
            env += f"  - {dep}\n"

        env += "  - pip\n"
        env += "  - pip:\n"
        for dep in runtime.pip_dependencies:
            env += f"    - {dep}\n"

        open(path, "w").write(env)

    @staticmethod
    def build_dockerfile(container: Container, path="Dockerfile"):
        dockerfile = f"FROM {container.image}:{container.tag}\n"
        dockerfile += "ADD environment.yml /tmp/environment.yml\n"
        dockerfile += "RUN conda env create -f /tmp/environment.yml\n"
        dockerfile += "RUN echo \"source activate env\" > ~/.bashrc\n"
        dockerfile += "ENV PATH /opt/conda/envs/env/bin:$PATH\n"
        open(path, "w").write(dockerfile)

    # def build_image(self, runtime: RunTime):
    #     """
    #     FROM continuumio/miniconda3
    #     ADD environment.yml /tmp/environment.yml
    #     RUN conda env create -f /tmp/environment.yml
    #     RUN echo "source activate env" > ~/.bashrc
    #     ENV PATH /opt/conda/envs/env/bin:$PATH
    #     """

    def register(self,
                 func,
                 runtime: RunTime = None,
                 container: Container = None,
                 resources: Resources = None):
        print(f"Registering variables: {func.__code__.co_varnames}")
        signature = inspect.signature(func)
        params = signature.parameters
        metadata = {
            "code": inspect.getsource(func),
            "sha256": hashlib.sha256(inspect.getsource(func).encode()).hexdigest(),
            "signature": str(signature),
            "variables": func.__code__.co_varnames,
            "annotations": str(func.__annotations__),
            "is_kwarg": [str(params[param].default) != "<class 'inspect._empty'>" for param in params],
            "pickle": codecs.encode(cloudpickle.dumps(func), "base64").decode(),
            "runtime": runtime.model_dump(),
            "container": container.model_dump(),
            "resources": resources.model_dump()
        }
        open(f"{self.path}/functions/{func.__name__}", "w").write(json.dumps(metadata))

        if runtime:
            self.build_image(runtime)

    def fn(self, func_name):
        metadata = json.loads(open(f"{self.path}/functions/{func_name}", "r").read())
        func = cloudpickle.loads(codecs.decode(metadata["pickle"].encode(), "base64"))
        return func

    def register_module(self, module):
        cloudpickle.register_pickle_by_value(module)
