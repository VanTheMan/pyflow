from pyflow.pyflow import Pyflow
from pyflow.storage import PyflowStorageObject
import pyflow_functions


pf = Pyflow()
pfn = pyflow_functions.PyflowFn(pf)

# Add way to inspect the function code
list(map(pfn.step2, [pfn.step1(1, 2), pfn.step1(3, 4)]))

pf.execute()

print(PyflowStorageObject(pf.executions[-1].output_path).load())
