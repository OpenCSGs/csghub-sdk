import logging

from pycsghub.file_download import file_download, snapshot_download_parallel

# Configure logging level
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# token = "your access token"
token = None

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'OpenCSG/csg-wukong-1B'
local_dir = "/Users/hhwang/temp/wukong"

print("=== Single-file multi-threaded download example ===")
result = file_download(
    repo_id,
    file_name='README.md',
    local_dir=local_dir,
    endpoint=endpoint,
    token=token,
    repo_type=repo_type,
    max_workers=4,
    use_parallel=True
)

print(f"Single-file multi-threaded downloaded ,save to: {result}")

print("\n=== Example of multi-threaded download for the entire repository ===")
cache_dir = "/Users/hhwang/temp/"
allow_patterns = ["*.json", "*.md", "*.txt"]

result = snapshot_download_parallel(
    repo_id,
    repo_type=repo_type,
    cache_dir=cache_dir,
    endpoint=endpoint,
    token=token,
    allow_patterns=allow_patterns,
    max_workers=6,
    use_parallel=True,  
    verbose=True 
)

print(f"Repository downloaded, save to: {result}")

print("\n=== Example of single-threaded download comparison ===")
# 使用单线程下载进行对比
result_single = file_download(
    repo_id,
    file_name='README.md',
    local_dir=local_dir,
    endpoint=endpoint,
    token=token,
    repo_type=repo_type,
    use_parallel=False
)

print(f"Single-threaded downloaded, save to: {result_single}")
