class PyflowFn:
    def __init__(self, pf):
        self.pf = pf

    def step2(self, step1_output):
        """step2(step1_output: pandas.core.frame.DataFrame) -> int"""
        return self.pf.function('step2')(step1_output)

    def step1(self, x, y, z=None, *args, **kwargs):
        """step1(x: int, y: int, z=1, *args, **kwargs) -> pandas.core.frame.DataFrame"""
        return self.pf.function('step1')(x, y, z=None, *args, **kwargs)

