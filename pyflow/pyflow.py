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

    def __init__(self, path: str = ".pyflow"):
        self.path = f"{Path.home()}/{path}"

    def get_function_path(self, func_name=None):
        if func_name is None:
            return f"{self.path}/functions"
        else:
            return f"{self.path}/functions/{func_name}"

    def get_conda_env_path(self, func_name=None):
        os.makedirs(f".pyflow/functions/{func_name}", exist_ok=True)
        return f".pyflow/functions/{func_name}/environment.yml"
        # return f"{self.path}/functions/{func_name}/environment.yml"

    def get_dockerfile_path(self, func_name=None):
        os.makedirs(f".pyflow/functions/{func_name}", exist_ok=True)
        return f".pyflow/functions/{func_name}/Dockerfile"
        # return f"{self.path}/functions/{func_name}/Dockerfile"

    def load_functions(self, annotate=False, path="pyflow_functions.py"):
        """
        This function will load all the functions in the functions directory and create a module.
        This module will have a class called PyflowFn. This class will have a function for each
        function in the function directory. Note that it is possible for this file to get
        out of sync with the function directory. So it is the user's responsibility to make sure
        that the functions directory and the module are in sync.

        :param annotate: Should the function be annotated with the type hints? If they are included,
            you will have to import the modules used in the annotations yourself.
        :param path: Where should the module be saved?
        :return:
        """
        if not os.path.exists(self.get_function_path()):
            os.makedirs(self.get_function_path())

        function_module = "class PyflowFn:\n"
        function_module += "    def __init__(self, pf):\n"
        function_module += "        self.pf = pf\n\n"

        for func in os.listdir(f"{self.path}/functions"):
            metadata = json.loads(open(f"{self.get_function_path(func)}/meta.json", "r").read())
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
        # TODO: write to pyflow directory and add to path
        open(path, "w").write(function_module)

    def build_conda_yml(self,
                        funtion_name: str,
                        runtime: RunTime):
        env = "name: env\n"
        env += "dependencies:\n"
        env += f"  - python={runtime.python_version.value}\n"
        for dep in runtime.conda_dependencies:
            env += f"  - {dep}\n"

        env += "  - pip\n"
        env += "  - pip:\n"
        for dep in runtime.pip_dependencies:
            env += f"    - {dep}\n"
        open(self.get_conda_env_path(funtion_name), "w").write(env)

    def build_dockerfile(self, funtion_name: str, container: Container):
        """
        Is it necessary to build an image here...can't you just use the base image and run
        all the necessary install instructions from a script using the command function...
        """
        dockerfile = f"FROM {container.image}:{container.tag}\n"
        dockerfile += f"ADD {self.get_conda_env_path(funtion_name)} /tmp/environment.yml\n"
        dockerfile += "RUN conda env create -f /tmp/environment.yml\n"
        dockerfile += "RUN echo \"source activate env\" > ~/.bashrc\n"
        dockerfile += "ENV PATH /opt/conda/envs/env/bin:$PATH\n"
        dockerfile += "ADD $PWD/ /root/\n"
        dockerfile += "WORKDIR /root/\n"
        dockerfile += "RUN pip install -e .\n"
        open(self.get_dockerfile_path(funtion_name), "w").write(dockerfile)

    def build_image(self,
                    funtion_name: str,
                    runtime: RunTime,
                    container: Container):
        self.build_conda_yml(funtion_name, runtime)
        self.build_dockerfile(funtion_name, container)
        os.system(f"docker build -t {funtion_name}:latest -f {self.path}/functions/{funtion_name}/Dockerfile .")

    def register(self,
                 func: callable,
                 runtime: RunTime = RunTime(),
                 container: Container = Container(),
                 resources: Resources = Resources()):
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

        os.makedirs(self.get_function_path(func.__name__), exist_ok=True)
        open(f"{self.get_function_path(func.__name__)}/meta.json", "w").write(json.dumps(metadata))

    def fn(self, func_name):
        metadata = json.loads(open(f"{self.path}/functions/{func_name}/meta.json", "r").read())
        func = cloudpickle.loads(codecs.decode(metadata["pickle"].encode(), "base64"))
        return func

    def register_module(self, module):
        cloudpickle.register_pickle_by_value(module)
