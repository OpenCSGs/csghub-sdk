import os
import requests
from typing import Optional
from pycsghub.constants import (DEFAULT_REVISION)
from pycsghub.utils import (build_csg_headers, get_endpoint)

def http_upload_file(
        repo_id: str,
        repo_type: Optional[str] = None,
        file_path: str = None,
        revision: Optional[str] = DEFAULT_REVISION,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
    ):
    if not os.path.exists(file_path):
        raise ValueError(f"file '{file_path}' does not exist")
    http_endpoint = endpoint if endpoint is not None else get_endpoint()
    if not http_endpoint.endswith("/"):
        http_endpoint += "/"
    http_url = http_endpoint + "api/v1/" + repo_type + "s/" + repo_id + "/upload_file"
    post_headers = build_csg_headers(token=token)
    file_data = {'file': open(file_path, 'rb')}
    form_data = {'file_path': file_path, 'branch': revision, 'message': 'upload' + file_path}
    response = requests.post(http_url, headers=post_headers, data=form_data, files=file_data)
    if response.status_code == 200:
        print(f"file '{file_path}' upload successfully.")
    else:
        print(f"fail to upload {file_path} with response code: {response.status_code}, error: {response.content.decode()}")
    