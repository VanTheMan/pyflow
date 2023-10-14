from pyflow.pyflow import Pyflow
import tests.some_module as some_module
from pyflow.config import PyFlowRunTime, PythonVersion, PyFlowContainer

pf = Pyflow()

rt = PyFlowRunTime(
    python_version=PythonVersion.v3_11,
    conda_dependencies=["pandas"],
    pip_dependencies=["numpy"],
    gpu=False
)

pf.register_module(some_module)


@pf.register(runtime=rt)
def step1(x: int, y: int, z=1, *args, **kwargs) -> int:
    print(f"step {x} {y}")
    some_module.plus(x, y)
    return x + y + z


@pf.register(runtime=rt)
def step2(x) -> int:
    print(x)
    return x + 1


step2(step1(1, 2))
pf.execute()
