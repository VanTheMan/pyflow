from pyflow.pyflow import Pyflow
from pyflow.config import RunTime, PythonVersion, Container

pf = Pyflow()

rt = RunTime(
    python_version=PythonVersion.v3_11,
    conda_dependencies=["pandas"],
    pip_dependencies=["numpy"],
    gpu=False
)

pf.build_image("step1", rt, Container())
pf.build_image("step2", rt, Container())
