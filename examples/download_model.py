from pycsghub.snapshot_download import snapshot_download
# token = "your access token"
token = None

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = "OpenCSG/csg-wukong-1B"
local_dir = "/Users/hhwang/temp/wukong"
allow_patterns = ["*.json"]
ignore_patterns = ["tokenizer.json"]

result = snapshot_download(
    repo_id, 
    repo_type=repo_type, 
    local_dir=local_dir, 
    endpoint=endpoint, 
    token=token,
    allow_patterns=allow_patterns,
    ignore_patterns=ignore_patterns)

print(f"Save model to {result}")

