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

# 使用pip安装训练相关的依赖
pip install "csghub-sdk[train]"
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

有关详细的命令行使用示例，包括下载模型/数据集、上传文件/文件夹、管理推理/微调实例等功能，请参阅我们的[命令行文档](doc/cli_cn.md)。

## SDK使用示例

有关详细的SDK使用示例，包括模型下载、数据集下载、文件上传、目录上传以及兼容huggingface的模型加载等功能，请参阅我们的[SDK文档](doc/sdk_cn.md)。

## 功能计划

1. 使用命令行工具的方式与CSGHub交互
2. CSGHub仓库的创建、修改等管理操作
3. 模型本地或在线部署
4. 模型本地或在线微调
