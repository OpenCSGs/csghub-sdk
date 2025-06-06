<p align="left">
    <a href="https://github.com/OpenCSGs/csghub-sdk">English</a> ｜ 中文
</p>

# CSGHub SDK
## 介绍

CSGHub SDK 是一个强大的 Python 客户端，专门设计用于与 CSGHub 服务器无缝交互。这个工具包旨在为 Python 开发者提供一个高效且直接的方法来操作和管理远程 CSGHub 实例。无论您是希望自动化任务、管理数据，还是将 CSGHub 功能集成到您的 Python 应用中，CSGHUB SDK 都提供了一整套功能，让您轻松实现目标。

## 主要特性

仅需几行代码即可无缝快速切换模型下载地址至[OpenCSG](https://opencsg.com/)，[提高模型下载速度](#快速切换下载地址)。

轻松连接并与您的 Python 代码中的 CSGHub 服务器实例交互。

全面的 API 覆盖：完全访问 CSGHub 服务器提供的广泛功能，确保您可以执行广泛的操作。

用户友好：设计简单，使其对初学者友好，同时对高级用户来说足够强大。

高效的数据管理：简化在您的 CSGHub 服务器上管理和操作数据的过程。

自动化就绪：自动化重复任务和过程，节省时间并减少人为错误的可能性。

开源：深入源代码，贡献并自定义 SDK 以适应您的特定需求。

主要功能包括：

1. 仓库下载（模型/数据集）
2. 仓库信息查询（与huggingface兼容）

## 获取Token

浏览器访问[OpenCSG](https://opencsg.com/)，点击右上角`注册`完成用户注册过程，使用已经注册成功的用户和密码登录[OpenCSG](https://opencsg.com/)，登录成功后在`账号设置`中找到[`Access Token`](https://opencsg.com/settings/access-token)来获取token。

## 入门

要开始使用 CSGHub SDK，请确保您的系统上安装了 Python。然后，您可以使用 pip 安装 SDK：

```python
pip install csghub-sdk
```

安装后，您可以开始将 SDK 导入到您的 Python 脚本中，以连接到您的 CSGHub 服务器：

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

### 快速切换下载地址

通过如下方式仅需将导入包名`transformers`修改为`pycsghub.repo_reader`并设置下载token，即可实现无缝快速切换模型下载地址

```python
os.environ['CSGHUB_TOKEN'] = 'token-of-your'
from pycsghub.repo_reader import AutoModelForCausalLM, AutoTokenizer
```

### 从源代码安装

```shell
git clone https://github.com/OpenCSGs/csghub-sdk.git
cd csghub-sdk
pip install .
```

您可以使用`pip install '.[train]'`来安装与模型和数据集相关的依赖，例如：
```shell
pip install '.[train]'
```

## 命令行使用示例

```shell
export CSGHUB_TOKEN=your_access_token

# 模型下载
csghub-cli download wanghh2000/myprivate1 

# 模型下载时允许'*.json'模式的文件并忽略'*_config.json'模式的文件
csghub-cli download wanghh2000/myprivate1 --allow-patterns "*.json" --ignore-patterns "*_config.json"

# 数据集下载
csghub-cli download wanghh2000/myds1 -t dataset

# 应用下载
csghub-cli download wanghh2000/space1 -t space

# 上传单个文件到仓库目录folder1
csghub-cli upload wanghh2000/myprivate1 abc/3.txt folder1

# 上传本地目录'/Users/hhwang/temp/jsonl'到仓库'wanghh2000/m01'的默认分支根目录下
csghub-cli upload wanghh2000/m01 /Users/hhwang/temp/jsonl

# 上传本地目录'/Users/hhwang/temp/jsonl' 到仓库'wanghh2000/m04'的v2分支根目录下使用token'xxxxxx'
csghub-cli upload wanghh2000/m04 /Users/hhwang/temp/jsonl -k xxxxxx --revision v2

# 上传本地目录'/Users/hhwang/temp/jsonl'到仓库'wanghh2000/m01'的v1分支的'test/files'目录下
csghub-cli upload wanghh2000/m01 /Users/hhwang/temp/jsonl test/files --revision v1

# 上传本地目录'/Users/hhwang/temp/jsonl'到仓库'wanghh2000/m01'的默认分支'test/files'目录下并使用指定token
csghub-cli upload wanghh2000/m01 /Users/hhwang/temp/jsonl test/files -k xxxxxx

# 列出用户wanghh2000的推理实例
csghub-cli inference list -u wanghh2000

# 启动ID为1358使用模型wanghh2000/Qwen2.5-0.5B-Instruct的推理实例
csghub-cli inference start wanghh2000/Qwen2.5-0.5B-Instruct 1358

# 停止ID为1358使用模型wanghh2000/Qwen2.5-0.5B-Instruct的推理实例
csghub-cli inference stop wanghh2000/Qwen2.5-0.5B-Instruct 1358

# 列出用户wanghh2000的微调实例
csghub-cli finetune list -u wanghh2000

# 启动ID为326使用模型OpenCSG/csg-wukong-1B的微调实例
csghub-cli finetune start OpenCSG/csg-wukong-1B 326

# 停止ID为326使用模型OpenCSG/csg-wukong-1B的微调实例
csghub-cli finetune stop OpenCSG/csg-wukong-1B 326

# 上传本地目录/Users/hhwang/temp/abc中的所有文件到远程仓库wanghh2003/model05
csghub-cli upload-large-folder wanghh2003/model05 /Users/hhwang/temp/abc
```

注意：csghub-cli upload 将在仓库和分支不存在时创建它们。默认分支为main。如果您想上传到特定分支，可以使用 --revision 选项。如果该分支不存在，将会被创建。如果分支已存在，文件将上传到该分支。

当使用`upload-large-folder`命令上传文件夹时，上传进度会在记录在上传目录`.cache`文件夹中用于支持断点续传，在上传完成前勿删除`.cache`文件夹。

文件默认下载路径为`~/.cache/csg/`

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


## 功能计划

1. 使用命令行工具下载仓库文件
2. 使用命令行工具的方式与CSGHub交互
3. CSGHub仓库的创建、修改等管理操作
4. 模型本地或在线部署
5. 模型本地或在线微调
6. 快速上传大文件夹到CSGHub仓库
