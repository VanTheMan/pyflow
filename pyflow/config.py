from pydantic import BaseModel
import enum


class PythonVersion(str, enum.Enum):
    v3_11: str = "3.11"
    v3_10: str = "3.10"
    v3_9: str = "3.9"
    v3_8: str = "3.8"


class PyFlowRunTime(BaseModel):
    python_version: PythonVersion = PythonVersion.v3_11
    conda_dependencies: list[str] = []
    pip_dependencies: list[str] = []
    gpu: bool = False


class PyFlowContainer(BaseModel):
    image: str = "continuumio/miniconda3"
    tag: str = "latest"


class PyFlowResources(BaseModel):
    cpu: str = "1"
    mem: str = "1Gi"
