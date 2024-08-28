from pycsghub.file_download import file_download
# token = "your access token"
token = None

endpoint = "https://hub.opencsg.com"
repo_type = "model"
repo_id = 'OpenCSG/csg-wukong-1B'
cache_dir = '/Users/hhwang/temp/'
result = file_download(repo_id, file_name='README.md', cache_dir=cache_dir, endpoint=endpoint, token=token, repo_type=repo_type)
