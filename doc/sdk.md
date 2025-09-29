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
