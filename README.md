<p align="left">
    English ｜ <a href="https://github.com/OpenCSGs/csghub-sdk/blob/main/README_cn.md">中文</a>
</p>

# CSGHub SDK
## Introduction

The CSGHub SDK is a powerful Python client specifically designed to interact seamlessly with the CSGHub server. This toolkit is engineered to provide Python developers with an efficient and straightforward method to operate and manage remote CSGHub instances. Whether you're looking to automate tasks, manage data, or integrate CSGHub functionalities into your Python applications, the CSGHub SDK offers a comprehensive set of features to accomplish your goals with ease.

## Key Features

With just a few lines of code, you can seamlessly and quickly switch the model download URL to [OpenCSG](https://opencsg.com/), [enhancing the download speed of models](#quickly-switch-download-urls).

Effortlessly connect and interact with CSGHub server instances from your Python code.

Comprehensive API Coverage: Full access to the wide array of functionalities provided by the CSGHub server, ensuring you can perform a broad spectrum of operations.

User-Friendly: Designed with simplicity in mind, making it accessible for beginners while powerful enough for advanced users.

Efficient Data Management: Streamline the process of managing and manipulating data on your CSGHub server.

Automation Ready: Automate repetitive tasks and processes, saving time and reducing the potential for human error.

Open Source: Dive into the source code, contribute, and customize the SDK to fit your specific needs.

The main functions are:

1. Repo downloading（model/dataset）
2. Repo information query（Compatible with huggingface）

**XNet Accelerated Transfer (New!)**: Next-generation storage and version control technology for large-scale AI/ML data.
- **Storage Optimization**: Significantly reduces storage costs (tested savings > 50%) via intelligent Content-Defined Chunking and deduplication.
- **High-Speed Transfer**: Incremental updates ensure only changed data chunks are transferred, boosting upload/download speeds by multiples.
- **Enabled by Default**: Automatically optimizes upload, download, and storage for LFS large files. To disable, set the environment variable `CSGHUB_DISABLE_XNET=true` to fallback to standard LFS mode.

## Get My Token

Visit [OpenCSG](https://opencsg.com/), click on Sign Up in the top right corner to complete the user registration process. Use the successfully registered username and password to log in to [OpenCSG](https://opencsg.com/). After logging in, find [Access Token](https://opencsg.com/settings/access-token) under Account Settings to obtain the token.

## Getting Started

To get started with the CSGHub SDK, ensure you have Python installed on your system. Then, you can install the SDK using pip:

```python
pip install csghub-sdk

# install with train dependencies
pip install "csghub-sdk[train]"
```

After installation, you can begin using the SDK to connect to your CSGHub server by importing it into your Python script:

```python
import os 
from pycsghub.repo_reader import AutoModelForCausalLM, AutoTokenizer

os.environ['CSGHUB_TOKEN'] = 'your_access_token'

mid = 'OpenCSG/csg-wukong-1B'
model = AutoModelForCausalLM.from_pretrained(mid)
tokenizer = AutoTokenizer.from_pretrained(mid)

inputs = tokenizer.encode("Write a short story", return_tensors="pt")
outputs = model.generate(inputs)
print('result: ',tokenizer.batch_decode(outputs))
```

### Quickly switch download URLs

By simply changing the import package name from `transformers` to `pycsghub.repo_reader` and setting the download token, you can seamlessly and quickly switch the model download URL.

```python
os.environ['CSGHUB_TOKEN'] = 'your_access_token'
from pycsghub.repo_reader import AutoModelForCausalLM, AutoTokenizer
```

### Install from source code

```shell
git clone https://github.com/OpenCSGs/csghub-sdk.git
cd csghub-sdk
pip install .
```

You can install the dependencies related to the model and dataset using `pip install '.[train]'`, for example:

```shell
pip install '.[train]'
```

## Use cases of command line

For detailed command line usage examples, including downloading models/datasets, uploading files/folders, and managing inference/fine-tuning instances, please refer to our [CLI documentation](doc/cli.md).

## Use cases of SDK

For detailed SDK usage examples, including model/dataset downloading, file uploading, directory uploading, and Hugging Face compatible model loading, please refer to our [SDK documentation](doc/sdk.md).

## Roadmap

1. Interacting with CSGHub via command-line tools
2. Management operations such as creation and modification of CSGHub repositories
3. Model deployment locally or online
4. Model fine-tuning locally or online