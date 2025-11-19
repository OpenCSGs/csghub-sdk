## Use cases of command line

```shell
# set env token on linux 
export CSGHUB_TOKEN=your_access_token

# set env token on window command
set CSGHUB_TOKEN=your_access_token

# set env token on window powershell
$env:CSGHUB_TOKEN="your_access_token"
```

### Example works for Linux and Window CMD

```shell
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

# auto upload large file in multi-part mode by 'git push' under working directory
csghub-cli lfs-enable-largefiles ./
```

### Example for Window Powershell

Due to differences in parameter parsing, please refer to the following commands when using Windows PowerShell.

```
# download model
csghub-cli download wanghh2000/MyMind-0.05B

# download model with allow patterns '*.json' and ignore '*_config.json' pattern of files
csghub-cli download wanghh2000/MyMind-0.05B --allow-patterns="*.json" --ignore-patterns="*_config.json"

# download dataset
csghub-cli download wanghh2000/data-refine2 -t dataset
```

Notes: 
- `csghub-cli upload` will create repo and its branch if they do not exist. The default branch is `main`. If you want to upload to a specific branch, you can use the `--revision` option. If the branch does not exist, it will be created. If the branch already exists, the files will be uploaded to that branch. 
- `csghub-cli upload` has a limitation of the file size to 4GB. If you need to upload larger files, you can use the `csghub-cli upload-large-folder` command.

When using the `upload-large-folder` command to upload a folder, the upload progress will be recorded in the `.cache` folder within the upload directory to support resumable uploads. Do not delete the `.cache` folder before the upload is complete.

Download location is `~/.cache/csg/` by default.
