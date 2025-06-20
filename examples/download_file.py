from pycsghub.file_download import file_download
# token = "your access token"
token = None

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'OpenCSG/csg-wukong-1B'
local_dir = "/Users/hhwang/temp/wukong"
result = file_download(
    repo_id, 
    file_name='README.md', 
    local_dir=local_dir, 
    endpoint=endpoint, 
    token=token, 
    repo_type=repo_type)

print(f"Save file to {result}")
