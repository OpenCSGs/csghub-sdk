import logging
from typing import Dict
from pycsghub.utils import (build_csg_headers, get_endpoint, model_id_to_group_owner_name)
import requests
import base64
from pycsghub.constants import GIT_ATTRIBUTES_CONTENT, DEFAULT_REVISION, DEFAULT_LICENCE, REPO_TYPE_SPACE

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
        action_endpoint = get_endpoint(endpoint=endpoint)
        req_headers = build_csg_headers(token=token)
        fetch_url = f"{action_endpoint}/api/v1/{repo_type}s/{repo_id}/preupload/{revision}"
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
        action_endpoint = get_endpoint(endpoint=endpoint)
        req_headers = build_csg_headers(token=token)
        batch_url = f"{action_endpoint}/{repo_type}s/{repo_id}.git/info/lfs/objects/batch"
        params = {"upload_id": upload_id}
        response = requests.post(batch_url, headers=req_headers, params=params, json=payload)
        if response.status_code != 200:
            logger.error(f"fetch LFS {local_file} batch info from {batch_url} response: {response.text}")
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
        action_endpoint = get_endpoint(endpoint=endpoint)
        req_headers = build_csg_headers(token=token)
        commit_url = f"{action_endpoint}/api/v1/{repo_type}s/{repo_id}/commit/{revision}"
        response = requests.post(url=commit_url, headers=req_headers, json=payload)
        if response.status_code != 200:
            logger.error(f"create files commit on {commit_url} response: {response.text}")
        response.raise_for_status()
        return response.json()

    def repo_branch_exists(
        self,
        repo_id: str,
        repo_type: str,
        revision: str,
        endpoint: str,
        token: str,
    ):
        """
        Check if repo and branch exists
        """
        action_endpoint = get_endpoint(endpoint=endpoint)
        req_headers = build_csg_headers(token=token, headers={
            "Content-Type": "application/json"
        })
        action_url = f"{action_endpoint}/api/v1/{repo_type}s/{repo_id}/branches"
        response = requests.get(action_url, headers=req_headers)
        logger.debug(f"fetch {repo_type} {repo_id} branches on {action_url} response: {response.text}")
        
        if response.status_code != 200:
            return False, False
        jsonRes = response.json()
        if jsonRes["msg"] != "OK":
            return False, False

        branches = jsonRes["data"]
        for b in branches:
            if b["name"] == revision:
                return True, True
        
        return True, False
        
    def create_new_branch(
        self,
        repo_id: str,
        repo_type: str,
        revision: str,
        endpoint: str,
        token: str,
    ):
        """
        Create branch
        """
        action_endpoint = get_endpoint(endpoint=endpoint)
        req_headers = build_csg_headers(token=token, headers={
            "Content-Type": "application/json"
        })
        action_url = f"{action_endpoint}/api/v1/{repo_type}s/{repo_id}/raw/.gitattributes"
        
        GIT_ATTRIBUTES_CONTENT_BASE64 = base64.b64encode(GIT_ATTRIBUTES_CONTENT.encode()).decode()

        data = {
            "message": f"create new branch {revision}",
            "new_branch": revision,
            "content": GIT_ATTRIBUTES_CONTENT_BASE64
        }
        
        response = requests.post(action_url, json=data, headers=req_headers)
        if response.status_code != 200:
            logger.error(f"create new branch {revision} for {repo_type} {repo_id} on {action_endpoint} response: {response.text}")
        response.raise_for_status()
        return response

    def create_new_repo(
        self,
        repo_id: str,
        repo_type: str,
        revision: str,
        endpoint: str,
        token: str,
    ):
        """
        Create new repo
        """        
        action_endpoint = get_endpoint(endpoint=endpoint)
        req_headers = build_csg_headers(token=token, headers={
            "Content-Type": "application/json"
        })
        action_url = f"{action_endpoint}/api/v1/{repo_type}s"
        namespace, name = model_id_to_group_owner_name(model_id=repo_id)
        data = {
            "namespace": namespace,
            "name": name,
            "nickname": name,
            "default_branch": DEFAULT_REVISION,
            "private": True,
            "license": DEFAULT_LICENCE,
        }
        
        if repo_type == REPO_TYPE_SPACE:
            resource_resp = self.get_space_resources(endpoint=endpoint)
            resources = resource_resp["data"]
            if resources is not None and len(resources) > 0:
                resource_id = resources[0]["id"]
                data["resource_id"] = resource_id
            else:
                raise ValueError(f"no any space resource found for create {repo_type} {repo_id}")
        
        response = requests.post(action_url, json=data, headers=req_headers)
        if response.status_code != 200:
            logger.error(f"create new {repo_type} {repo_id} on {action_endpoint} response: {response.text}")
        response.raise_for_status()
        return response.json()

    def get_space_resources(
        self,
        endpoint: str,
    ):
        """
        Get space resources
        """
        action_endpoint = get_endpoint(endpoint=endpoint)
        req_headers = {
            "Content-Type": "application/json"
        }
        action_url = f"{action_endpoint}/api/v1/space_resources"
        params = {"deploy_type": "0"}
        response = requests.get(action_url, params=params, headers=req_headers)
        if response.status_code != 200:
            logger.error(f"query space resources on {action_endpoint} response: {response.text}")
        response.raise_for_status()
        return response.json()
