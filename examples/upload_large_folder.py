from pycsghub.upload_large_folder.main import upload_large_folder_internal

upload_large_folder_internal(
    repo_id="wanghh2000/ds16",
    local_path="/Users/hhwang/temp/bbb",
    repo_type="dataset",
    revision="v1",
    endpoint="https://hub.opencsg.com",
    token="my-token",
    allow_patterns=None,
    ignore_patterns=None,
    num_workers=1,
    print_report=False,
    print_report_every=1,
)
