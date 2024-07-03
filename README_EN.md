<p align="left">
    <a href="README_EN.md">English</a> ｜ 中文
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

## Getting Started

To get started with the CSGHub SDK, ensure you have Python installed on your system. Then, you can install the SDK using pip:

```python
pip install csghub-sdk
```

After installation, you can begin using the SDK to connect to your CSGHub server by importing it into your Python script:

```python
import os 
from pycsghub.repo_reader import AutoModelForCausalLM, AutoTokenizer

os.environ['CSG_TOKEN'] = 'f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf'

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
os.environ['CSG_TOKEN'] = 'token-of-your'
from pycsghub.repo_reader import AutoModelForCausalLM, AutoTokenizer
```
Get My Token from [OpenCSG](https://opencsg.com/settings/access-token)

### Install from source code

```shell
git clone https://github.com/OpenCSGs/csghub-sdk.git
cd csghub-sdk
pip install .
```

## Use cases

For more detailed instructions, including API documentation and usage examples, please refer to the Use case.

### Download single file

Use `http_get` function to download single file

```python
from pycsghub.file_download import http_get
token = "f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf"

url = "https://hub.opencsg.com/api/v1/models/OpenCSG/csg-wukong-1B/resolve/tokenizer.model"
local_dir = '/home/test/'
file_name = 'test.txt'
headers = None
cookies = None
http_get(url=url,
         token=token,
         local_dir=local_dir,
         file_name=file_name,
         headers=headers,
         cookies=cookies)
```

### Download single file

use `file_download` function to download single file from a repository

```python
from pycsghub.file_download import file_download
token = "f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf"

endpoint = "https://hub.opencsg.com"
repo_id = 'OpenCSG/csg-wukong-1B'
cache_dir = '/home/test/'
result = file_download(repo_id,
                       file_name='README.md',
                       cache_dir=cache_dir,
                       endpoint=endpoint,
                       token=token)
```

### Download repository

```python
from pycsghub.snapshot_download import snapshot_download
token = "f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf"

endpoint = "https://hub.opencsg.com"
repo_id = 'OpenCSG/csg-wukong-1B'
cache_dir = '/Users/hhwang/temp/'
result = snapshot_download(repo_id,
                           cache_dir=cache_dir,
                           endpoint=endpoint,
                           token=token)
```

### Model loading compatible with huggingface

The transformers library supports directly inputting the repo_id from Hugging Face to download and load related models, as shown below:

```python
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```

In this code, the Hugging Face Transformers library first downloads the model to a local cache folder, then reads the configuration, and loads the model by dynamically selecting the relevant class for instantiation.

To ensure compatibility with Hugging Face, version 0.2 of the CSGHub SDK now includes the most commonly features: downloading and loading models. Models can be downloaded and loaded as follows:

```python
# import os 
# os.environ['CSG_TOKEN'] = 'token_to_set'
from pycsghub.repo_reader import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```

This code: 

1. Use the `snapshot_download` from the CSGHub SDK library to download the related files.

2. By generating batch classes dynamically and using class name reflection mechanism, a large number of classes with the same names as those automatically loaded by transformers are created in batches.

3. Assign it with the from_pretrained method, so the model read out will be an hf-transformers model.

## Roadmap

1. Dataset Download
2. Interacting with CSGHub via command-line tools
3. Management operations such as creation and modification of CSGHub repositories
4. Model deployment locally or online
5. Model fine-tuning locally or online
6. Publishing the model to a remote hosting repository
