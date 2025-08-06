from pycsghub.snapshot_download import snapshot_download

# token = "your access token"
token = None

endpoint = "https://hub.opencsg.com"
repo_id = "OpenDataLab/CodeExp"
repo_type = "dataset"
cache_dir = "/Users/hhwang/temp/"
allow_patterns = ["*.json"]
result = snapshot_download(repo_id, repo_type=repo_type, cache_dir=cache_dir, endpoint=endpoint, token=token,
                           allow_patterns=allow_patterns)
