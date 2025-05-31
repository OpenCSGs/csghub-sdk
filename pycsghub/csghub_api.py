import logging
from typing import Dict
from pycsghub.utils import (build_csg_headers, get_endpoint)
import requests

logger = logging.getLogger(__name__)

class CsgHubApi:
    '''
    csghub API wrapper class
    '''

    def __init__(self):
        pass

    def fetch_upload_modes(
        self,
        payload: Dict,
        repo_id: str,
        repo_type: str,
        revision: str,
        endpoint: str,
        token: str,
    ):
        """
        Requests repo files upload modes
        """
        http_endpoint = endpoint if endpoint is not None else get_endpoint()
        req_headers = build_csg_headers(token=token)
        fetch_url = f"{http_endpoint}/api/v1/{repo_type}s/{repo_id}/preupload/{revision}"
        response = requests.post(fetch_url, headers=req_headers, json=payload)
        if response.status_code != 200:
            logger.error(f"fetch upload modes from {fetch_url} response: {response.text}")
        response.raise_for_status()
        return response.json()

    def fetch_lfs_batch_info(
        self,
        payload: Dict,
        repo_id: str,
        repo_type: str,
        revision: str,
        endpoint: str,
        token: str,
        local_file: str,
        upload_id: str,
    ):
        """
        Requests the LFS batch endpoint to retrieve upload instructions
        """
        http_endpoint = endpoint if endpoint is not None else get_endpoint()
        req_headers = build_csg_headers(token=token)
        batch_url = f"{http_endpoint}/{repo_type}s/{repo_id}.git/info/lfs/objects/batch"
        params = {"upload_id": upload_id}
        response = requests.post(batch_url, headers=req_headers, params=params, json=payload)
        if response.status_code != 200:
            logger.error(f"fetch lfs {local_file} batch info from {batch_url} response: {response.text}")
        response.raise_for_status()
        return response.json()
    
    def create_commit(
        self,
        payload: Dict,
        repo_id: str,
        repo_type: str,
        revision: str,
        endpoint: str,
        token: str,        
    ):
        """
        Creates a commit in the given repo, deleting & uploading files as needed.
        """
        http_endpoint = endpoint if endpoint is not None else get_endpoint()
        req_headers = build_csg_headers(token=token)
        commit_url = f"{http_endpoint}/api/v1/{repo_type}s/{repo_id}/commit/{revision}"
        response = requests.post(url=commit_url, headers=req_headers, json=payload)
        if response.status_code != 200:
            logger.error(f"create files commit {commit_url} response: {response.text}")
        response.raise_for_status()
        return response.json()
        