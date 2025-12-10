"""
CSGHub SDK setup configuration
"""
from setuptools import setup

def get_version() -> str:
    rel_path = "pycsghub/__init__.py"
    with open(rel_path, "r") as fp:
        for line in fp.read().splitlines():
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

# This file is now mainly used for backward compatibility
# The main configuration has been moved to pyproject.toml

if __name__ == "__main__":
    setup(
        version=get_version(),
        description="Client library to download and publish models, datasets and other repos on the opencsg.com hub",
        long_description=open("README.md").read()
    )
