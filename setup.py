from setuptools import setup, find_packages

setup(
    name="bulkRNASeq",
    version="0.2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "rich>=10.0.0",
        "pyyaml>=5.4.1",
        "tqdm>=4.65.0",
    ],
    python_requires=">=3.8",
) 