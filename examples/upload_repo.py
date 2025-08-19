import logging
from pycsghub.repository import Repository

# token = "your access token"
token = None

# set log level
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)

r = Repository(
    repo_id="wanghh2000/ds16",
    upload_path="/Users/hhwang/temp/bbb/jsonl",
    user_name="wanghh2000",
    token=token,
    repo_type="dataset",
)

r.upload()