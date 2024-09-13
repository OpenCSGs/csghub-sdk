from pycsghub.snapshot_download import snapshot_download
# token = "your access token"
token = None

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'OpenCSG/csg-wukong-1B'
cache_dir = '/Users/hhwang/temp/'
result = snapshot_download(repo_id, repo_type=repo_type, cache_dir=cache_dir, endpoint=endpoint, token=token)