import logging
from pycsghub.repository import Repository

token = "your access token"

# set log level
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)

# for dataset
r = Repository(
    repo_id="wanghh2000/dataset16",
    upload_path="/Users/hhwang/temp/bbb",
    user_name="wanghh2000",
    token=token,
    repo_type="dataset",
)

# for space
r = Repository(
    repo_id="wanghh2000/space16",
    upload_path="/Users/hhwang/temp/bbb",
    user_name="wanghh2000",
    token=token,
    repo_type="space",
    sdk="gradio",
    resource_id=4,
    cluster_id="xxxx-xxxx-xxxx-xxxx",
    min_replica=1,
)

r.upload()