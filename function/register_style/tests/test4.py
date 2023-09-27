import inspect


def bla(x: str,
        y: str,
        z: int = 1,
        *args,
        **kwargs
        ) -> str:
    """

    :param x:
    :param y:
    :param z:
    :param args:
    :param kwargs:
    :return:
    """
    print("asd")


# help(bla)

# print(bla.__code__.co_varnames)
# print(bla.__annotations__)
# print(bla.__annotations__["return"])
print(inspect.getsource(bla))
print()
# print(inspect.signature(bla).parameters)
# params = inspect.signature(bla).parameters
# print(next(params))
# print([params[param].default for param in params])
# print([str(params[param].default) != "<class 'inspect._empty'>" for param in params],)
# print(params["z"])