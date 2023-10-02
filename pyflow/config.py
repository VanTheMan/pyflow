from pydantic import BaseModel
import enum


class PythonVersion(enum.Enum):
    v3_11: str = "3.11"
    v3_10: str = "3.10"
    v3_9: str = "3.9"
    v3_8: str = "3.8"


class RunTime(BaseModel):
    python_version: PythonVersion = PythonVersion.v3_11
    conda_dependencies: list[str]
    pip_dependencies: list[str]
    gpu: bool


class Container(BaseModel):
    image: str = "continuumio/miniconda3"
    tag: str = "latest"


class Resources(BaseModel):
    cpu: str
    mem: str
