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

```shell
export CSGHUB_TOKEN=your_access_token

# download model
csghub-cli download OpenCSG/csg-wukong-1B

# download model with allow patterns '*.json' and ignore '*_config.json' pattern of files
csghub-cli download OpenCSG/csg-wukong-1B --allow-patterns "*.json" --ignore-patterns "tokenizer.json"

# download model with ignore patterns '*.json' and '*.bin' pattern of files to /Users/hhwang/temp/wukong
csghub-cli download OpenCSG/csg-wukong-1B --allow-patterns "*.json" --ignore-patterns "tokenizer.json" --local-dir /Users/hhwang/temp/wukong

# download dataset
csghub-cli download OpenCSG/GitLab-DataSets-V1 -t dataset

# download space
csghub-cli download OpenCSG/csg-wukong-1B -t space

# upload local large folder '/Users/hhwang/temp/abc' to model repo 'wanghh2000/model05'
csghub-cli upload-large-folder wanghh2000/model05 /Users/hhwang/temp/abc

# list inference instances for user 'wanghh2000'
csghub-cli inference list -u wanghh2000

# start inference instance for model repo 'wanghh2000/Qwen2.5-0.5B-Instruct' with ID '1358'
csghub-cli inference start wanghh2000/Qwen2.5-0.5B-Instruct 1358

# stop inference instance for model repo 'wanghh2000/Qwen2.5-0.5B-Instruct' with ID '1358'
csghub-cli inference stop wanghh2000/Qwen2.5-0.5B-Instruct 1358

# list fine-tuning instances for user 'wanghh2000'
csghub-cli finetune list -u wanghh2000

# start fine-tuning instance for model repo 'OpenCSG/csg-wukong-1B' with ID '326'
csghub-cli finetune start OpenCSG/csg-wukong-1B 326

# stop fine-tuning instance for model repo 'OpenCSG/csg-wukong-1B' with ID '326'
csghub-cli finetune stop OpenCSG/csg-wukong-1B 326

# upload a single file to folder1
csghub-cli upload wanghh2000/myprivate1 abc/3.txt folder1

# upload local folder '/Users/hhwang/temp/jsonl' to root path of repo 'wanghh2000/m01' with default branch
csghub-cli upload wanghh2000/m01 /Users/hhwang/temp/jsonl

# upload local folder '/Users/hhwang/temp/jsonl' to root path of repo 'wanghh2000/m04' with token 'xxxxxx' and v2 branch
csghub-cli upload wanghh2000/m04 /Users/hhwang/temp/jsonl -k xxxxxx --revision v2

# upload local folder '/Users/hhwang/temp/jsonl' to path 'test/files' of repo 'wanghh2000/m01' with branch v1
csghub-cli upload wanghh2000/m01 /Users/hhwang/temp/jsonl test/files --revision v1

# upload local folder '/Users/hhwang/temp/jsonl' to path 'test/files' of repo 'wanghh2000/m01' with token 'xxxxxx'
csghub-cli upload wanghh2000/m01 /Users/hhwang/temp/jsonl test/files -k xxxxxx
```

Notes: 
- `csghub-cli upload` will create repo and its branch if they do not exist. The default branch is `main`. If you want to upload to a specific branch, you can use the `--revision` option. If the branch does not exist, it will be created. If the branch already exists, the files will be uploaded to that branch. 
- `csghub-cli upload` has a limitation of the file size to 4GB. If you need to upload larger files, you can use the `csghub-cli upload-large-folder` command.

When using the `upload-large-folder` command to upload a folder, the upload progress will be recorded in the `.cache` folder within the upload directory to support resumable uploads. Do not delete the `.cache` folder before the upload is complete.

Download location is `~/.cache/csg/` by default.

## Use cases of SDK

For more detailed instructions, including API documentation and usage examples, please refer to the Use case.

### Download model

```python
from pycsghub.snapshot_download import snapshot_download
token = "your_access_token"

endpoint = "https://hub.opencsg.com"
repo_id = 'OpenCSG/csg-wukong-1B'
cache_dir = '/Users/hhwang/temp/'
result = snapshot_download(repo_id, cache_dir=cache_dir, endpoint=endpoint, token=token)
```

### Download model with allow patterns '*.json' and ignore '*_config.json' pattern of files

```python
from pycsghub.snapshot_download import snapshot_download
token = "your_access_token"

endpoint = "https://hub.opencsg.com"
repo_id = 'OpenCSG/csg-wukong-1B'
cache_dir = '/Users/hhwang/temp/'
allow_patterns = ["*.json"]
ignore_patterns = ["*_config.json"]
result = snapshot_download(repo_id, cache_dir=cache_dir, endpoint=endpoint, token=token, allow_patterns=allow_patterns, ignore_patterns=ignore_patterns)
```

### Download dataset 
```python
from pycsghub.snapshot_download import snapshot_download
token="xxxx"
endpoint = "https://hub.opencsg.com"
repo_id = 'AIWizards/tmmluplus'
repo_type="dataset"
cache_dir = '/Users/xiangzhen/Downloads/'
result = snapshot_download(repo_id, repo_type=repo_type, cache_dir=cache_dir, endpoint=endpoint, token=token)
```

### Download single file

Use `http_get` function to download single file

```python
from pycsghub.file_download import http_get
token = "your_access_token"

url = "https://hub.opencsg.com/api/v1/models/OpenCSG/csg-wukong-1B/resolve/tokenizer.model"
local_dir = '/home/test/'
file_name = 'test.txt'
headers = None
cookies = None
http_get(url=url, token=token, local_dir=local_dir, file_name=file_name, headers=headers, cookies=cookies)
```

use `file_download` function to download single file from a repository

```python
from pycsghub.file_download import file_download
token = "your_access_token"

endpoint = "https://hub.opencsg.com"
repo_id = 'OpenCSG/csg-wukong-1B'
cache_dir = '/home/test/'
result = file_download(repo_id, file_name='README.md', cache_dir=cache_dir, endpoint=endpoint, token=token)
```

### Upload file

```python
from pycsghub.file_upload import http_upload_file

token = "your_access_token"

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'wanghh2000/myprivate1'
result = http_upload_file(repo_id, endpoint=endpoint, token=token, repo_type='model', file_path='test1.txt')
```

### Upload multi-files

```python
from pycsghub.file_upload import http_upload_file

token = "your_access_token"

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'wanghh2000/myprivate1'

repo_files = ["1.txt", "2.txt"]
for item in repo_files:
    http_upload_file(repo_id=repo_id, repo_type=repo_type, file_path=item, endpoint=endpoint, token=token)
```

### Upload the local path to repo

Before starting, please make sure you have Git-LFS installed (see [here](https://git-lfs.github.com/) for installation instructions).

```python
from pycsghub.repository import Repository

token = "your access token"

r = Repository(
    repo_id="wanghh2003/ds15",
    upload_path="/Users/hhwang/temp/bbb/jsonl",
    user_name="wanghh2003",
    token=token,
    repo_type="dataset",
)

r.upload()
```

### Upload the local path to the specified path in the repo

Before starting, please make sure you have Git-LFS installed (see [here](https://git-lfs.github.com/) for installation instructions).

```python
from pycsghub.repository import Repository

token = "your access token"

r = Repository(
    repo_id="wanghh2000/model01",
    upload_path="/Users/hhwang/temp/jsonl",
    path_in_repo="test/abc",
    user_name="wanghh2000",
    token=token,
    repo_type="model",
    branch_name="v1",
)

r.upload()
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
# os.environ['CSGHUB_TOKEN'] = 'your_access_token'
from pycsghub.repo_reader import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```

This code: 

1. Use the `snapshot_download` from the CSGHub SDK library to download the related files.

2. By generating batch classes dynamically and using class name reflection mechanism, a large number of classes with the same names as those automatically loaded by transformers are created in batches.

3. Assign it with the from_pretrained method, so the model read out will be an hf-transformers model.

## Roadmap

1. Interacting with CSGHub via command-line tools
2. Management operations such as creation and modification of CSGHub repositories
3. Model deployment locally or online
4. Model fine-tuning locally or online
