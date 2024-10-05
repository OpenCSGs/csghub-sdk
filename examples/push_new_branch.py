from pycsghub.repository import Repository

# token = "your access token"
token = None

r = Repository(
    repo_id="wanghh2003/ds8",
    work_dir="/Users/hhwang/temp/ccc",
    user_name="wanghh2003",
    token=token,
    repo_type="dataset"
)

r.upload_as_new_branch(
    new_branch_name="v6", 
    upload_path="/Users/hhwang/temp/bbb/jsonl",
    uploadPath_as_repoPath=True
)