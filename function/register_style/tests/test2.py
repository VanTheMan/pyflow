from function.register_style.function_register_style import Pyflow
import pyflow_functions
import inspect

pf = Pyflow()
pfn = pyflow_functions.PyflowFn(pf)

# Add way to inspect the function code

df = pfn.step2(pfn.step1(1, 2))
print(df)
