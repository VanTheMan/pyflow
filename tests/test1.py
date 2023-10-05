from pyflow.pyflow import Pyflow
import some_module

pf = Pyflow()


def step1(x: int, y: int, z=1, *args, **kwargs) -> int:
    print(f"step {x} {y}")
    some_module.plus(x, y)
    return x + y + z


def step2(x) -> int:
    print(x)
    return x + 1


pf.register_module(some_module)
pf.register(step1)
pf.register(step2)
