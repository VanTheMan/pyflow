import pandas


class PyflowFn:
    def __init__(self, pf):
        self.pf = pf

    def step2(self, step1_output: pandas.core.frame.DataFrame) -> int:
        return self.pf.function('step2')(step1_output)

    def step1(self, x: int, y: int) -> pandas.core.frame.DataFrame:
        return self.pf.function('step1')(x, y)

