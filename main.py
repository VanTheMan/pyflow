from abc import ABC, abstractmethod


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


class Job(ABC):

    def __init__(self,
                 runtime: RunTime,
                 container: Container,
                 resources: Resources,
                 *args):
        self.container = self.get_container_from_runtime(runtime) if runtime else container

    def get_container_from_runtime(self, runtime: RunTime):
        return Container(
            image=f"python:{runtime.python}",
            tag=f"py{runtime.python}-gpu" if runtime.gpu else f"py{runtime.python}",
        )

    @abstractmethod
    def execute(self, **kwargs):
        pass

    def __call__(self, **kwargs):
        self.execute(**kwargs)
        # Store all args for provenance
        # Store all outputs for provenance


class Job1(Job):

    def __init__(self,
                 runtime: RunTime,
                 container: Container,
                 resources: Resources):
        super().__init__(runtime, container, resources)
        self.output = None

    def execute(self):
        print("Hello World!")
        self.output = "Some beautiful output!"


class Job2(Job):

    def __init__(self,
                 runtime: RunTime,
                 container: Container,
                 resources: Resources,
                 job1: Job1):
        super().__init__(runtime, container, resources)
        self.job1 = job1

    def execute(self):
        print(f"The output from the previous job is {self.job1.output}")


job1 = Job1().execute()
job2 = Job2(job1)
# Or
job2 = Job2(Job1.last_execution())