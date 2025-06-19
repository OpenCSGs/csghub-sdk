from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='csghub-sdk',
    version='0.7.1',
    author="opencsg",
    author_email="contact@opencsg.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include="pycsghub*"),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "csghub-cli=pycsghub.cli:app",
        ]
    },
    install_requires=[
        "typer",
        "typing_extensions",
        "huggingface_hub>=0.22.2",
    ],
    extras_require={
        "train": [
            "torch",
            "transformers>=4.33.3",
            "datasets>=2.20.0"
        ],
    },
    python_requires=">=3.8,<3.14",
)
