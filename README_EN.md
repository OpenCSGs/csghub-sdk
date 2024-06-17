<p align="left">
    <a href="README_EN.md">English</a> ｜ 中文
</p>

# CSGHUB_SDK
## 介绍
csghub_sdk is the python client designed for csghub_server, to facilitate users using python code 
to operate remote csghub
The main contents included are:

1. Repo downloading（model/dataset）
2. Repo information query（ Compatible with huggingface）
3. Repo uploading
4. Repo information update


## RoadMap


## Use cases

### Downloading single file
use `http_get` function to download single file
```python

from pycsghub.file_download import http_get
token = "f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9" + \
        "b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf"

url = "https://hub-stg.opencsg.com/api/v1/models/wayne0019/lwfmodel/resolve/lfsfile.bin"
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
use `file_download` function to download single file from a rep

```python
from pycsghub.file_download import file_download
token = "f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9" + \
        "b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf"
endpoint = "https://hub-stg.opencsg.com"
repo_id = 'wayne0019/lwfmodel'
cache_dir = '/home/test'
result = file_download(repo_id,
                       file_name='README.md',
                       cache_dir=cache_dir,
                       endpoint=endpoint,
                       token=token)

```

### Repo download

```python
from pycsghub.snapshot_download import snapshot_download
token = "f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9" + \
        "b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf"
endpoint = "https://hub-stg.opencsg.com"
repo_id = 'wayne0019/lwfmodel'
cache_dir = '/home/test'
result = snapshot_download(repo_id,
                           cache_dir=cache_dir,
                           endpoint=endpoint,
                           token=token)
```


### Install

```shell
git clone thisrepo

cd thisrepo

pip install .

```


### Model loading compatible with huggingface


The transformers library supports directly inputting the repo_id on huggingface to download and load 
related models, as shown below:
```python
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```
In this code, transformer library of huggingface first downloads the model to the local cache folder, then reads the 
configuration, and loads the model by reflecting to the relevant class for loading.

In order to be compatible with huggingface, the V0.1 version of cshhubsdk also provides users with the most 
commonly used functions, model downloading and loading. And the model can be downloaded and loaded in the 
following ways.
```python
# 注意首先要进行环境变量设置，因为下载需要token，下述api的调用，会直接在环境变量中查找相应的token。
# import os 
# os.environ['CSG_TOKEN'] = 'token_to_set'
from pycsghub.repo_reader import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```

This code: 1. Call snapshotdownload of the pycsghub library to download relevant files; 2. Create a large number
of automatic model loading classes for pycsghub.repo_reader in batches through dynamic batch class generation and
class reflection mechanisms. And give it the from_pretrained method. The model read in this way is the 
hf-transformers model.



