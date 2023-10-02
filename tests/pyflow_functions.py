class PyflowFn:
    def __init__(self, pf):
        self.pf = pf

    def step2(self, x):
        """step2(x) -> int"""
        return self.pf.fn('step2')(x)

    def step1(self, x, y, z=None, *args, **kwargs):
        """step1(x: int, y: int, z=1, *args, **kwargs) -> list"""
        return self.pf.fn('step1')(x, y, z=z, *args, **kwargs)

