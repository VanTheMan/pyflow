class PythonVersion:
    v3_11 = "3.11"
    v3_10 = "3.10"
    v3_9 = "3.9"
    v3_8 = "3.8"


class RunTime:

    def __init__(self,
                 python_version: PythonVersion,
                 requirements: list[str],
                 gpu: bool = False):
        self.python_version = python_version
        self.requirements = requirements
        self.gpu = gpu


class Container:

    def __init__(self,
                 image: str,
                 tag: str):
        self.image = image
        self.tag = tag


class Resources:

    def __init__(self,
                 cpu: str,
                 mem: str):
        self.cpu = cpu
        self.mem = mem
