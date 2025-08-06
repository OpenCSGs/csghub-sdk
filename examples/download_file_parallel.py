import logging

from pycsghub.file_download import file_download, snapshot_download_parallel

# 配置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# token = "your access token"
token = None

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'OpenCSG/csg-wukong-1B'
local_dir = "/Users/hhwang/temp/wukong"

print("=== 单文件多线程下载示例 ===")
result = file_download(
    repo_id,
    file_name='README.md',
    local_dir=local_dir,
    endpoint=endpoint,
    token=token,
    repo_type=repo_type,
    max_workers=4,  # 设置线程数
    use_parallel=True  # 启用多线程下载
)

print(f"单文件下载完成，保存到: {result}")

print("\n=== 整个仓库多线程下载示例 ===")
cache_dir = "/Users/hhwang/temp/"
allow_patterns = ["*.json", "*.md", "*.txt"]  # 只下载特定类型的文件

result = snapshot_download_parallel(
    repo_id,
    repo_type=repo_type,
    cache_dir=cache_dir,
    endpoint=endpoint,
    token=token,
    allow_patterns=allow_patterns,
    max_workers=6,  # 设置更多线程数用于批量下载
    use_parallel=True,  # 启用多线程下载
    verbose=True  # 启用详细日志
)

print(f"仓库下载完成，保存到: {result}")

print("\n=== 单线程下载对比示例 ===")
# 使用单线程下载进行对比
result_single = file_download(
    repo_id,
    file_name='README.md',
    local_dir=local_dir,
    endpoint=endpoint,
    token=token,
    repo_type=repo_type,
    use_parallel=False  # 禁用多线程，使用原有单线程下载
)

print(f"单线程下载完成，保存到: {result_single}")
