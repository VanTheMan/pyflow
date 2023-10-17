import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyflow",
    version="0.0.1",
    author="Van Zyl van Vuuren",
    author_email="",
    description="A package for building and running python workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pydantic",
        "cloudpickle",
        'hera',
    ]
)
