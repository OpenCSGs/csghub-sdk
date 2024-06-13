<p align="left">
    <a href="README_EN.md">English</a> ｜ 中文
</p>

# CSGHUB_SDK
## 介绍
csghub_sdk是csghub_server的python client,旨在方便用户利用python代码对远程的csghub进行操作
其中包括的主体内容有：
1. 库下载（模型/数据集）
2. 库读取（输出模型兼容huggingface）
3. 库上传
4. server实例信息查询与更改等
## 设计理念
csghubserver是一个repo

## RoadMap
初步计划5月底前完成下载与部分库查询接口，见飞书文档
二期完成下载模型的库加载

6月开发规划
1. repo信息查询，
2. repo信息增删改查
3. 模型上传
4. 通过cshhubapi调用所有接口


## 使用示例

### 单文件下载
使用http_get接口进行单文件下载
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

使用file_download 封装接口进行单文件下载
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

### 库下载

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


### 本repo安装

```shell
git clone thisrepo

cd thisrepo

pip install .

```


### 兼容huggingface的模型加载

huggingface的transformers库支持直接输入huggingface上的repo_id以下载并读取相关模型，如下列所示：
```python
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```
在这段代码中，hf的transformer库首先下载模型到本地cache文件夹中，然后读取配置，并通过反射到相关类进行加载的方式加载模型。

cshhubsdkV0.1版本为了兼容huggingface也提供用户最常用的功能，模型下载与加载。并可以通过如下的方式进行模型下载与加载
```python
# 注意首先要进行环境变量设置，因为下载需要token，下述api的调用，会直接在环境变量中查找相应的token。
# import os 
# os.environ['CSG_TOKEN'] = 'token_to_set'
from pycsghub.repo_reader import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('model/repoid')
```

这段代码首先：1. 调用pycsghub库的snaphotdownload下载相关文件；2.通过动态批量类生成与类名反射机制，批量为pycsghub.repo_reader创建大量与transformers自动类加载的重名类。并为其赋予from_pretrained方法。这样读取出来的模型即为hf-transformers模型。




