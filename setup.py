from setuptools import setup, find_packages

setup(
    name="bulkRNASeq",
    version="0.2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
) 