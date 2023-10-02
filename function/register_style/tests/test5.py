from function.register_style.function_register_style import Pyflow
from utils import RunTime, PythonVersion, Container

rt = RunTime(
    python_version=PythonVersion.v3_11,
    conda_dependencies=["pandas"],
    pip_dependencies=["numpy"],
    gpu=False
)

Pyflow.build_conda_yml(rt, path="environment.yml")
Pyflow.build_dockerfile(Container(), path="Dockerfile")
