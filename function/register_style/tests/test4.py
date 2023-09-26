import inspect


def bla(x: str,
        y: str,
        z: None,
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
#
# print(bla.__annotations__["x"])
# print(bla.__annotations__["return"])
# print(inspect.getsource(bla))
print(inspect.signature(bla).return_annotation)