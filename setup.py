from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='csghub-sdk',
    version='0.3.9',
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
        "typer>=0.12.3",
        "attr>=0.3.2",
        "ConfigParser>=7.0.0",
        "contextlib2>=21.6.0",
        "cryptography>=43.0.1",
        "Cython>=3.0.10",
        "dl>=0.1.0",
        "docutils>=0.21.2",
        "HTMLParser>=0.0.2",
        "huggingface_hub>=0.22.2",
        "ipython>=8.12.3",
        "ipywidgets>=8.1.2",
        "keyring>=25.2.1",
        "lockfile>=0.12.2",
        "mock>=5.1.0",
        "Pillow>=10.3.0",
        "protobuf>=5.27.0",
        "pyOpenSSL>=24.1.0",
        "railroad>=0.5.0",
        "Sphinx>=7.3.7",
        "thread>=2.0.3",
        "tornado>=6.4.1",
        "tqdm>=4.66.3",
        "trove_classifiers>=2024.5.22",
        "truststore>=0.9.1",
        "urllib3_secure_extra>=0.1.0",
    ],
    extras_require={
        "train": [
            "torch",
            "transformers>=4.33.3",
            "datasets>=2.20.0"
        ],
    },
    python_requires=">=3.10",
)
