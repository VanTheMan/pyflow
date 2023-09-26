import cloudpickle

from function.register_style.function_register_style import Pyflow
import pandas as pd
import some_module

pf = Pyflow()


def step1(x: int, y: int):
    print(f"step {x} {y}")
    some_module.plus(x, y)
    return pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})


def step2(step1_output: pd.DataFrame):
    print(step1_output.columns)
    return 2


pf.register_module(some_module)
pf.register(step1)
pf.register(step2)
