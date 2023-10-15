from hera.workflows import Steps, Workflow, WorkflowsService, script, Container, Resources, HostPathVolume
import os
from pathlib import Path


@script()
def echo(message: str):
    print(message)


PYFLOW_HOME = os.getenv("PYFLOW_HOME", f"{Path.home()}/.pyflow")

with Workflow(
        generate_name="hello-world-",
        entrypoint="my-steps",
        namespace="argo",
        workflows_service=WorkflowsService(host="https://localhost:2746", verify_ssl=False),
        volumes=[HostPathVolume(
            name="pyflow",
            path="/.pyflow",
            type="Directory"
        )]
) as w:
    c = Container(
        name="c",
        image="alpine:3.7",
        command=["sh", "-c"],
        args=["echo Hello, world!"],
        volume_mounts=[{
            "name": "pyflow",
            "mount_path": "/root/.pyflow",
        }],
    )

    with Steps(name="my-steps") as s:
        c(name="step1")
        c(name="step2")

w.create()
# w.wait()
