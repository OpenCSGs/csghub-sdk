import os
from typing import Optional

import requests

from pycsghub.constants import (DEFAULT_REVISION)
from pycsghub.utils import (build_csg_headers, get_endpoint)


def http_upload_file(
        repo_id: str,
        repo_type: Optional[str] = None,
        file_path: str = None,
        path_in_repo: Optional[str] = "",
        revision: Optional[str] = DEFAULT_REVISION,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        verbose: bool = False,
):
    if verbose:
        print(f"[DEBUG] Starting file upload...")
        print(f"[DEBUG] File path: {file_path}")
        print(f"[DEBUG] Repo ID: {repo_id}")
        print(f"[DEBUG] Repo type: {repo_type}")
        print(f"[DEBUG] Path in repo: {path_in_repo}")
        print(f"[DEBUG] Revision: {revision}")
        print(f"[DEBUG] Endpoint: {endpoint}")
    
    if not os.path.exists(file_path):
        raise ValueError(f"file '{file_path}' does not exist")
    
    destination_path = os.path.join(path_in_repo, os.path.basename(file_path)) if path_in_repo else file_path
    http_endpoint = endpoint if endpoint is not None else get_endpoint()
    if not http_endpoint.endswith("/"):
        http_endpoint += "/"
    http_url = http_endpoint + "api/v1/" + repo_type + "s/" + repo_id + "/upload_file"
    
    if verbose:
        print(f"[DEBUG] HTTP URL: {http_url}")
        print(f"[DEBUG] Destination path: {destination_path}")
    
    post_headers = build_csg_headers(token=token)
    file_data = {'file': open(file_path, 'rb')}
    form_data = {'file_path': destination_path, 'branch': revision, 'message': 'upload' + file_path}
    
    if verbose:
        print(f"[DEBUG] Sending POST request...")
    
    response = requests.post(http_url, headers=post_headers, data=form_data, files=file_data)
    
    if verbose:
        print(f"[DEBUG] Response status code: {response.status_code}")
        print(f"[DEBUG] Response content: {response.content.decode()}")
    
    if response.status_code == 200:
        print(f"file '{file_path}' upload successfully.")
    else:
        print(
            f"fail to upload {file_path} with response code: {response.status_code}, error: {response.content.decode()}")
