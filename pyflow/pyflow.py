import copy

import cloudpickle
import json
import os
from pathlib import Path
import codecs
import inspect
import hashlib
from pyflow.config import RunTime, Container, Resources


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

    def create_init_script(self):
        # Create a script that will be run when the container starts. This script will
        # activate the conda environment, install all the requirements and then run the
        # function.
        pass

    @staticmethod
    def build_dockerfile(container: Container, path="Dockerfile"):
        """
        Is it necessary to build an image here...can't you just use the base image and run
        all the necessary install instructions from a script using the command function...
        """
        dockerfile = f"FROM {container.image}:{container.tag}\n"
        # Use init script to install all the requirements and then run the function
        # This means you can reuse a container for multiple runs, but will you have
        # access to all the repos...tbd. The run will alos not be reproducable
        # because the container will be updated with the latest packages.
        dockerfile += "ADD environment.yml /tmp/environment.yml\n"
        dockerfile += "RUN conda env create -f /tmp/environment.yml\n"
        dockerfile += "RUN echo \"source activate env\" > ~/.bashrc\n"
        dockerfile += "ENV PATH /opt/conda/envs/env/bin:$PATH\n"
        dockerfile += "ADD $PWD/ /root/\n"
        dockerfile += "WORKDIR /root/\n"
        dockerfile += "RUN pip install -e .\n"
        open(path, "w").write(dockerfile)

    @staticmethod
    def build_image(image_name: str,
                    function_version: int,
                    runtime: RunTime,
                    container: Container):
        Pyflow.build_conda_yml(runtime, path="environment.yml")
        Pyflow.build_dockerfile(container, path="Dockerfile")
        os.system(f"docker build -t {image_name}:{function_version} .")

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

    def fn(self, func_name):
        metadata = json.loads(open(f"{self.path}/functions/{func_name}", "r").read())
        func = cloudpickle.loads(codecs.decode(metadata["pickle"].encode(), "base64"))
        return func

    def register_module(self, module):
        cloudpickle.register_pickle_by_value(module)
