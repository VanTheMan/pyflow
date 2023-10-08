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

STORAGE_OBJECT_PREFIX = "PYFLOW_OBJECT_"
PYFLOW_HOME = os.getenv("PYFLOW_HOME", f"{Path.home()}/.pyflow")


class OutputPath:

    def __init__(self, path):
        self.base_path = path.replace(STORAGE_OBJECT_PREFIX, '').replace(PYFLOW_HOME, '')

    def __str__(self):
        return STORAGE_OBJECT_PREFIX + self.base_path

    def full_path(self):
        return PYFLOW_HOME + self.base_path

    @staticmethod
    def check(path):
        """
        Check if the path is an output path.
        :param path:
        :return:
        """
        return STORAGE_OBJECT_PREFIX in path


class FnStub:

    def __init__(self, func_name, execution_id, output_path: OutputPath, *args, **kwargs):
        self.func_name = func_name
        self.args = args
        self.kwargs = kwargs
        self.execution_id = execution_id
        self._output_path = output_path

    @property
    def output_path(self):
        return self._output_path.full_path()


class Pyflow:

    def __init__(self):
        self.flow_home_path = PYFLOW_HOME
        self.executions: list[FnStub] = []

    def _add_home_dir(self, path):
        return f"{self.flow_home_path}/{path}"

    def _check_path(self, path):
        os.makedirs(path, exist_ok=True)
        return path

    def _get_base_function_path(self, func_name=None):
        if func_name is None:
            return "functions"
        else:
            return f"functions/{func_name}"

    def _get_function_path(self, func_name=None):
        return self._check_path(self._add_home_dir(self._get_base_function_path(func_name)))

    def _get_function_storage_path(self, func_name=None, execution_id=None):
        path = self._check_path(f"{self._get_function_path(func_name)}/{execution_id}")
        return path + "/storage.pkl"

    def _get_conda_env_path(self, func_name=None):
        path = self._check_path(".pyflow/" + self._get_function_path(func_name))
        return path + "/environment.yml"

    def _get_dockerfile_path(self, func_name=None):
        path = self._check_path(".pyflow/" + self._get_function_path(func_name))
        return path + "/Dockerfile"

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
        function_module = "class PyflowFn:\n"
        function_module += "    def __init__(self, pf):\n"
        function_module += "        self.pf = pf\n\n"

        for func in os.listdir(f"{self.flow_home_path}/functions"):
            metadata = json.loads(open(f"{self._get_function_path(func)}/meta.json", "r").read())
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

    def _build_conda_yml(self,
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
        open(self._get_conda_env_path(funtion_name), "w").write(env)

    def _build_dockerfile(self, funtion_name: str, container: Container):
        """
        Is it necessary to build an image here...can't you just use the base image and run
        all the necessary install instructions from a script using the command function...
        """
        dockerfile = f"FROM {container.image}:{container.tag}\n"
        dockerfile += f"ADD {self._get_conda_env_path(funtion_name)} /tmp/environment.yml\n"
        dockerfile += "RUN conda env create -f /tmp/environment.yml\n"
        dockerfile += "RUN echo \"source activate env\" > ~/.bashrc\n"
        dockerfile += "ENV PATH /opt/conda/envs/env/bin:$PATH\n"
        dockerfile += "ADD $PWD/ /root/\n"
        dockerfile += "WORKDIR /root/\n"
        dockerfile += "RUN pip install -e .\n"
        open(self._get_dockerfile_path(funtion_name), "w").write(dockerfile)

    def build_image(self,
                    funtion_name: str,
                    runtime: RunTime,
                    container: Container):
        self._build_conda_yml(funtion_name, runtime)
        self._build_dockerfile(funtion_name, container)
        os.system(f"docker build -t {funtion_name}:latest -f {self._get_dockerfile_path(funtion_name)} .")

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

        os.makedirs(self._get_function_path(func.__name__), exist_ok=True)
        open(f"{self._get_function_path(func.__name__)}/meta.json", "w").write(json.dumps(metadata))
        # Figure out how to build from .pyflow directory
        # Might need to have more than one docker context?
        # self.build_image(func.__name__, runtime, container)

    def execute(self):
        for execution in self.executions:
            parsed_args = ""
            for arg in execution.args:
                # Add quotes around strings
                parsed_args += f"\'{arg}\', " if type(arg) == str or type(arg) == OutputPath else f"{arg}, "

            # TODO fix kwargs = None
            # if len(execution.kwargs) > 0:
            # parsed_args += ", ".join([f"{k}={v}" for k, v in execution.kwargs.items()])

            docker_command = f"docker run "
            docker_command += f"-v $HOME/.pyflow:/root/.pyflow "
            docker_command += f"-e EXECUTION_ID={execution.execution_id} "
            docker_command += f"{execution.func_name} "

            inline_python = f"from pyflow.pyflow import Pyflow; "
            inline_python += f"Pyflow().load_fn('{execution.func_name}')({parsed_args}); "

            docker_command += f"python -c \"{inline_python}\""
            os.system(docker_command)

    def load_fn(self, func_name):
        """
        Load the function from the function path. The function is wrapped with functionality to
        load the arguments and store the output of the function in the storage path.

        :param func_name:
        :return:
        """
        metadata = json.loads(open(f"{self._get_function_path(func_name)}/meta.json", "r").read())
        func = cloudpickle.loads(codecs.decode(metadata["pickle"].encode(), "base64"))

        def func_storage_wrapper(*args, **kwargs):
            parsed_args = []
            for arg in args:
                if type(arg) == str and OutputPath.check(arg):
                    parsed_args.append(
                        PyflowStorageObject(OutputPath(arg).full_path()).load())
                else:
                    parsed_args.append(arg)
            parsed_args = tuple(parsed_args)
            execution_id = os.getenv("EXECUTION_ID")
            outputs = func(*parsed_args, **kwargs)
            storage_object = PyflowStorageObject(self._get_function_storage_path(func_name, execution_id))
            storage_object.dump(outputs)
            # TODO: Add return type meta data
            return storage_object

        return func_storage_wrapper

    def fn(self, func_name):
        """
        Create a stub for the function call and add it to the list of executions.

        :param func_name:
        :return: A function that will create a stub for the function call and add it to the list of
            executions.
        """

        def schedule(*args, **kwargs):
            """
            This function will be called when the user calls a function. It will
            create a stub for the function call and add it to the list of executions. The stub will
            contain the function name, the arguments, the keyword arguments and the output path.

            :param func_name:
            :return: The output path of the function call, that can be passed as an argument to
                another function call.
            """
            execution_id = time.time_ns()
            output_path = OutputPath(self._get_function_storage_path(func_name, execution_id))
            stub = FnStub(func_name, execution_id, output_path, *args, **kwargs)
            self.executions.append(stub)
            return output_path

        return schedule

    def register_module(self, module):
        cloudpickle.register_pickle_by_value(module)
