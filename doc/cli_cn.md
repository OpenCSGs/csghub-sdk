## 命令行使用示例

```shell
export CSGHUB_TOKEN=your_access_token

# 模型下载
csghub-cli download OpenCSG/csg-wukong-1B

# 模型下载时允许'*.json'模式的文件并忽略'*_config.json'模式的文件
csghub-cli download OpenCSG/csg-wukong-1B --allow-patterns "*.json" --ignore-patterns "*_config.json"

# 模型下载时允许'*.json'模式的文件并忽略'*_config.json'模式的文件到本地目录'/Users/hhwang/temp/wukong'
csghub-cli download OpenCSG/csg-wukong-1B --allow-patterns "*.json" --ignore-patterns "tokenizer.json" --local-dir /Users/hhwang/temp/wukong

# 数据集下载
csghub-cli download OpenCSG/chinese-fineweb-edu-v2 -t dataset

# 应用下载
csghub-cli download OpenCSG/csg-wukong-1B -t space

# 上传本地目录/Users/hhwang/temp/abc中的所有文件到远程仓库wanghh2000/model05
csghub-cli upload-large-folder wanghh2000/model05 /Users/hhwang/temp/abc

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

# 在当前工作目录启用大文件分片上传功能
csghub-cli lfs-enable-largefiles ./

```

注意：
- `csghub-cli upload` 将在仓库和分支不存在时创建它们。默认分支为main。如果您想上传到特定分支，可以使用 --revision 选项。如果该分支不存在，将会被创建。如果分支已存在，文件将上传到该分支。
- `csghub-cli upload` 限制文件大小为4GB。如果您需要上传更大的文件，可以使用`csghub-cli upload-large-folder` 命令.

当使用`upload-large-folder`命令上传文件夹时，上传进度会在记录在上传目录`.cache`文件夹中用于支持断点续传，在上传完成前勿删除`.cache`文件夹。

文件默认下载路径为`~/.cache/csg/`
