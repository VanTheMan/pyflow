from pyflow.pyflow import Pyflow
import pyflow_functions

pf = Pyflow()
pfn = pyflow_functions.PyflowFn(pf)

# Add way to inspect the function code
df = list(map(pfn.step2, pfn.step1(1, 2)))

# Figure out how to do map with containers and remote storage.
print(df)
