from function.register_style.function_register_style import Pyflow
import inspect

pf = Pyflow()

# You can register a function, class, file, or directory
print(pf.functions)

print(inspect.getsource(pf.function("step1")))
df = pf.function("step2")(pf.function("step1")(1, 2))
print(df)
