from pyflow.pyflow import Pyflow
import some_module

pf = Pyflow()


def step1(x: int, y: int, z=1, *args, **kwargs) -> list:
    print(f"step {x} {y}")
    some_module.plus(x, y)
    return [1, 2, 3, 4]


def step2(x) -> int:
    print(x)
    return sum(x)


pf.register_module(some_module)
pf.register(step1)
pf.register(step2)
