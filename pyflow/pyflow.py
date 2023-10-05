import copy
import time

import cloudpickle
import json
import os
from pathlib import Path
import codecs
import inspect
import hashlib
from pyflow.config import RunTime, Container, Resources
from pyflow.storage import PyflowStorageObject


class Pyflow:

    def __init__(self, path: str = ".pyflow"):
        self.path = f"{Path.home()}/{path}"
        self.executions = []

    def get_function_path(self, func_name=None):
        if func_name is None:
            return f"{self.path}/functions"
        else:
            return f"{self.path}/functions/{func_name}"

    def get_function_storage_path(self, func_name=None, execution_id=None):
        os.makedirs(self.get_function_path(func_name) + f"/{execution_id}", exist_ok=True)
        return self.get_function_path(func_name) + f"/{execution_id}/storage.pkl"

    def get_conda_env_path(self, func_name=None):
        os.makedirs(f".pyflow/functions/{func_name}", exist_ok=True)
        return f".pyflow/functions/{func_name}/environment.yml"

    def get_dockerfile_path(self, func_name=None):
        os.makedirs(f".pyflow/functions/{func_name}", exist_ok=True)
        return f".pyflow/functions/{func_name}/Dockerfile"

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
        os.system(f"docker build -t {funtion_name}:latest -f {self.get_dockerfile_path(funtion_name)} .")

    def register(self,
                 func: callable,
                 runtime: RunTime = RunTime(),
                 container: Container = Container(),
                 resources: Resources = Resources()):
        print(f"Registering variables: {func.__code__.co_varnames}")
        signature = inspect.signature(func)
        params = signature.parameters
        metadata = {
            "name": func.__name__,
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
        # Figure out how to build from .pyflow directory
        # Might need to have more than one docker context?
        # self.build_image(func.__name__, runtime, container)

    class FnStub:

        def __init__(self, func_name, execution_id, output_path, *args, **kwargs):
            self.func_name = func_name
            self.args = args
            self.kwargs = kwargs
            self.execution_id = execution_id
            self.output_path = output_path

    def schedule(self, func_name: str):

        def schedule_wrapper(*args, **kwargs):
            execution_id = time.time_ns()
            output_path = self.get_function_storage_path(func_name, execution_id)
            stub = self.FnStub(func_name, execution_id, output_path, *args, **kwargs)
            self.executions.append(stub)
            return output_path

        return schedule_wrapper

    def execute(self):
        for execution in self.executions:
            parsed_args = ", ".join([str(arg) for arg in execution.args])
            # if len(execution.kwargs) > 0:
                # parsed_args += ", "
                # TODO fix kwargs = None
                # parsed_args += ", ".join([f"{k}={v}" for k, v in execution.kwargs.items()])
            parsed_args += f", execution_id={execution.execution_id}"

            inline_python = f"from pyflow.pyflow import Pyflow; Pyflow().get_fn('{execution.func_name}')({parsed_args})"

            command = f"docker run -v $HOME/.pyflow:/root/.pyflow {execution.func_name} python -c \"{inline_python}\""
            os.system(command)

    def get_fn(self, func_name):
        metadata = json.loads(open(f"{self.path}/functions/{func_name}/meta.json", "r").read())
        func = cloudpickle.loads(codecs.decode(metadata["pickle"].encode(), "base64"))

        def func_storage_wrapper(*args, **kwargs):
            parsed_args = []
            for arg in args:
                if type(arg) == str and ".pyflow/" in arg:
                    parsed_args.append(PyflowStorageObject(arg).load())
                else:
                    parsed_args.append(arg)
            parsed_args = tuple(parsed_args)
            execution_id = kwargs.pop("execution_id")
            outputs = func(*parsed_args, **kwargs)
            storage_object = PyflowStorageObject(self.get_function_storage_path(func_name, execution_id))
            storage_object.dump(outputs)
            # TODO: Add return type meta data
            return storage_object

        return func_storage_wrapper

    def fn(self, func_name):
        return self.schedule(func_name)

    def register_module(self, module):
        cloudpickle.register_pickle_by_value(module)
