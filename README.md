# CSGHUB
## 介绍
csghub 是一款opencsg公司，csghub_server的python client旨在方便用户利用python代码对远程的csghub进行操作
其中包括的主体内容有：
1. 库下载（模型/数据集）
2. 库读取（输出模型兼容huggingface）
3. 库上传
4. server实例信息查询与更改等


## RoadMap
初步计划5月底前完成下载与部分库查询接口，见飞书文档
二期完成下载模型的库加载


## 使用示例

### 单文件下载

```python

from csg_hub.file_download import http_get
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


### 库下载

```python
from csg_hub.snapshot_download import snapshot_download
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

