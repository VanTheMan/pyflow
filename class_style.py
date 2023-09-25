from utils import RunTime, Container, Resources
from abc import ABC, abstractmethod

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
# Historical execution
# job_objects = list_job_objects()
job2 = Job2(Job1.last_execution())