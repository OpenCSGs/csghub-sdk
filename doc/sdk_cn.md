## SDK使用示例

### 模型下载

```python
from pycsghub.snapshot_download import snapshot_download
token = "your_access_token"

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'OpenCSG/csg-wukong-1B'
cache_dir = '/Users/hhwang/temp/'
result = snapshot_download(repo_id, repo_type=repo_type, cache_dir=cache_dir, endpoint=endpoint, token=token,)
```

### 模型下载时允许'*.json'模式的文件并忽略'*_config.json'模式的文件

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

### 数据集下载
```python
from pycsghub.snapshot_download import snapshot_download
token = "your_access_token"

endpoint = "https://hub.opencsg.com"
repo_id = 'AIWizards/tmmluplus'
repo_type = "dataset"
cache_dir = '/Users/xiangzhen/Downloads/'
result = snapshot_download(repo_id, repo_type=repo_type, cache_dir=cache_dir, endpoint=endpoint, token=token)
```

### 单文件下载

使用`file_download`封装接口进行单文件下载

```python
from pycsghub.file_download import file_download
token = "your_access_token"

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'OpenCSG/csg-wukong-1B'
cache_dir = '/home/test/'
result = file_download(repo_id, file_name='README.md', cache_dir=cache_dir, endpoint=endpoint, token=token, repo_type=repo_type)
```

使用`http_get`接口进行单文件下载

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

### 单文件上传

```python
from pycsghub.file_upload import http_upload_file

token = "your_access_token"

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'wanghh2000/myprivate1'
result = http_upload_file(repo_id, endpoint=endpoint, token=token, repo_type='model', file_path='test1.txt')
```

### 多文件上传

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

### 上传本地目录到仓库

在开始之前，请确保您已安装 Git-LFS（安装说明请参见 [这里](https://git-lfs.github.com/)）。

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

### 上传本地目录到仓库的指定目录

在开始之前，请确保您已安装 Git-LFS（安装说明请参见 [这里](https://git-lfs.github.com/)）。

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

### 兼容huggingface的模型加载

huggingface的transformers库支持直接输入huggingface上的repo_id以下载并读取相关模型，如下列所示：

```
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```

在这段代码中，hf的transformer库首先下载模型到本地cache文件夹中，然后读取配置，并通过反射到相关类进行加载的方式加载模型。

CSGHub SDK v0.2版本为了兼容huggingface也提供用户最常用的功能，模型下载与加载。并可以通过如下的方式进行模型下载与加载

```python
# 注意首先要进行环境变量设置，因为下载需要token，下述api的调用，会直接在环境变量中查找相应的token。
# import os 
# os.environ['CSGHUB_TOKEN'] = 'your_access_token'
from pycsghub.repo_reader import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```

这段代码首先：

1. 调用CSGHub SDK库的`snapshot_download`下载相关文件。

2. 通过动态批量类生成与类名反射机制，批量创建大量与transformers自动类加载的重名类。

3. 为其赋予from_pretrained方法，这样读取出来的模型即为hf-transformers模型。
