# AGENTS Guidelines

The CSGHub SDK is a powerful Python client specifically designed to interact seamlessly with the CSGHub server. This toolkit is engineered to provide Python developers with an efficient and straightforward method to operate and manage remote CSGHub instances. Whether you're looking to automate tasks, manage data, or integrate CSGHub functionalities into your Python applications, the CSGHub SDK offers a comprehensive set of features to accomplish your goals with ease.

# Structure

This is standard python project and can be upload to PYPI.

- **doc** is documents for how to use python sdk.
- **pycsghub** is all code for function logic.
- **pycsghub/cmd** is command line definition.
- **pycssghub/constants.py** is for save all constants variable.

## Code Style & Conventions

- Cods must following python standard code style.
- Use rest api for invoke remote api server.
- Must add log for function execute.
- All sdk command line must support show help to explain parameters.

## samples

- `examples/download_dataset.py` is for download dataset by sdk.
- `examples/download_file.py` is for download file from csghub by sdk.
- `examples/download_model.py` is for download model from csghub by sdk.
- `examples/load_dataset.py` is for load dataset from local by sdk.
- `examples/upload_ifle.py` is for upload file to remote server.
- `examples/upload_large_folder.py` is for upload large folder by sdk.
- `examples/upload_repo.py` is for upload local file to remote repo.

## Build

- Use `uv pip install .` to install sdk locally.
- Use `python setup.py check` to check the python package.
- Use `python setup.py sdist bdist_wheel` to build python package for new version.

## Specific Instructions

- There are 2 languages help documents in English and Chinese.
- Update document by new feature code changes.
