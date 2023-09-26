class PyflowFn:
    def __init__(self, pf):
        self.pf = pf

    def step2(self, step1_output):
        return self.pf.function('step2')(step1_output)

    def step1(self, x, y):
        return self.pf.function('step1')(x, y)

