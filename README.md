<p align="left">
    <a href="https://github.com/OpenCSGs/csghub-sdk/blob/main/README_EN.md">English</a> ｜ 中文
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

os.environ['CSG_TOKEN'] = '3b77c98077b415ca381ded189b86d5df226e3776'

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
os.environ['CSG_TOKEN'] = 'token-of-your'
from pycsghub.repo_reader import AutoModelForCausalLM, AutoTokenizer
```

### 从源代码安装

```shell
git clone https://github.com/OpenCSGs/csghub-sdk.git
cd csghub-sdk
pip install .
```

## 命令行使用示例

```shell
export CSG_TOKEN=your_access_token

# 模型下载
csghub-cli download wanghh2000/myprivate1 

# 数据集下载
csghub-cli download wanghh2000/myds1 -t dataset

# 上传单个文件
csghub-cli upload wanghh2000/myprivate1 abc/3.txt

# 上传多个文件
csghub-cli upload wanghh2000/myds1 abc/4.txt abc/5.txt -t dataset 
```

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
# os.environ['CSG_TOKEN'] = 'token_to_set'
from pycsghub.repo_reader import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```

这段代码首先：

1. 调用CSGHub SDK库的`snapshot_download`下载相关文件。

2. 通过动态批量类生成与类名反射机制，批量创建大量与transformers自动类加载的重名类。

3. 为其赋予from_pretrained方法，这样读取出来的模型即为hf-transformers模型。


## 功能计划

1. 数据集下载
2. 使用命令行工具的方式与CSGHub交互
3. CSGHub仓库的创建、修改等管理操作
4. 模型本地或在线部署
5. 模型本地或在线微调
6. 模型发布到远程托管仓库


