from pyflow.pyflow import Pyflow
from pyflow.config import RunTime, PythonVersion, Container

rt = RunTime(
    python_version=PythonVersion.v3_11,
    conda_dependencies=["pandas"],
    pip_dependencies=["numpy"],
    gpu=False
)

Pyflow.build_image("pyflow_test_fn", 1, rt, Container())
