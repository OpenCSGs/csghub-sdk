import os
from typing import Optional
import subprocess
from typing import List, Optional, Union
from pathlib import Path
import requests
import base64
import shutil
import re
from urllib.parse import urlparse
from pycsghub.constants import GIT_ATTRIBUTES_CONTENT, REPO_TYPE_DATASET
from pycsghub.utils import (build_csg_headers,
                            model_id_to_group_owner_name,
                            get_endpoint)

class Repository:
    def __init__(
        self,
        repo_id: str,
        work_dir: str,
        user_name: str,
        token: str,
        license: Optional[str] = "apache-2.0",
        nickname: Optional[str] = "",
        description: Optional[str] = "",
        repo_type: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        if work_dir is None:
            raise ValueError("work dir is None")
    
        if not os.path.exists(work_dir):
            raise ValueError("work dir is not a valid path")
        
        self.repo_id = repo_id
        self.work_dir = work_dir
        self.user_name = user_name
        self.token = token
        self.license = license
        self.nickname = nickname
        self.description = description
        self.repo_type = repo_type
        self.endpoint = endpoint
        if self.repo_type == REPO_TYPE_DATASET:
            self.repo_url_prefix = "datasets"
        else:
            self.repo_url_prefix = "models"
        self.namespace, self.name = model_id_to_group_owner_name(model_id=self.repo_id)
        self.repo_dir = os.path.join(self.work_dir, self.name)

    def upload_as_new_branch(
        self, 
        branch_name: str, 
        upload_path: str,
        uploadPath_as_repoPath: bool = False,
    ) -> str:
        if branch_name is None:
            raise ValueError("new branch name is None")
        
        if not os.path.exists(upload_path):
           raise ValueError("src_path does not exist")
        
        response = self.create_new_branch(branch_name=branch_name)
        if response.status_code != 200:
            raise ValueError(f"fail to request new branch {branch_name} for {self.repo_id}")
        
        json_response = response.json()
        if json_response["msg"] != "OK":
            raise ValueError(f"fail to create new branch {branch_name} for {self.repo_id}")
        
        if os.path.exists(self.repo_dir):
            shutil.rmtree(self.repo_dir)
        
        repo_url = self.generate_repo_clone_url()
        self.git_clone(branch_name=branch_name, repo_url=repo_url)
        
        from_path = ""
        git_cmd_workdir = ""
        if uploadPath_as_repoPath:
            from_path = self.repo_dir
            git_cmd_workdir = upload_path
        else:
            from_path = upload_path
            git_cmd_workdir = self.repo_dir
        
        shutil.copytree(from_path, git_cmd_workdir, dirs_exist_ok=True)
        
        self.git_add(work_dir=git_cmd_workdir)
        self.git_commit(work_dir=git_cmd_workdir)
        number_of_commits = self.commits_to_push(work_dir=git_cmd_workdir)
        if number_of_commits > 1:
            self.git_push(work_dir=git_cmd_workdir)

    def create_new_branch(
        self,
        branch_name: str,
        ):
        action_endpoint = get_endpoint(endpoint=self.endpoint)
        url = f"{action_endpoint}/api/v1/{self.repo_url_prefix}/{self.repo_id}/raw/.gitattributes"
        
        GIT_ATTRIBUTES_CONTENT_BASE64 = base64.b64encode(GIT_ATTRIBUTES_CONTENT.encode()).decode()

        data = {
            "message": f"create new branch {branch_name} by data flow",
            "new_branch": branch_name,
            "content": GIT_ATTRIBUTES_CONTENT_BASE64
        }
        
        headers = build_csg_headers(token=self.token, headers={
            "Content-Type": "application/json"
        })
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response

    def upload_as_new_repo(
        self,
        upload_path: str,
        uploadPath_as_repoPath: bool = False,
        ) -> None:
        if not os.path.exists(upload_path):
           raise ValueError("src_path does not exist")
       
        response = self.create_new_repo()
        if response.status_code != 200:
            raise ValueError(f"fail to create new repo for {self.repo_id}")
        
        repo_url = self.generate_repo_clone_url()
        self.git_clone(branch_name="main", repo_url=repo_url)
        
        from_path = ""
        git_cmd_workdir = ""
        if uploadPath_as_repoPath:
            from_path = self.repo_dir
            git_cmd_workdir = upload_path
        else:
            from_path = upload_path
            git_cmd_workdir = self.repo_dir
        
        shutil.copytree(from_path, git_cmd_workdir, dirs_exist_ok=True)
        
        self.git_add(work_dir=git_cmd_workdir)
        self.git_commit(work_dir=git_cmd_workdir)
        number_of_commits = self.commits_to_push(work_dir=git_cmd_workdir)
        if number_of_commits > 1:
            self.git_push(work_dir=git_cmd_workdir)

        
    def create_new_repo(
        self,
        ):
        action_endpoint = get_endpoint(endpoint=self.endpoint)
        url = f"{action_endpoint}/api/v1/{self.repo_url_prefix}"

        data = {
            "namespace": self.namespace,
            "name": self.name,
            "nickname": self.nickname,
            "default_branch": "main",
            "private": True,
            "license": self.license,
            "description": self.description,
        }
        
        headers = build_csg_headers(token=self.token, headers={
            "Content-Type": "application/json"
        })
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response

    def generate_repo_clone_url(self) -> str:
        clone_endpoint = get_endpoint(endpoint=self.endpoint)
        clone_url = f"{clone_endpoint}/{self.repo_url_prefix}/{self.repo_id}.git"
        scheme = urlparse(clone_url).scheme
        clone_url = clone_url.replace(f"{scheme}://", f"{scheme}://{self.user_name}:{self.token}@")
        return clone_url

    def git_clone(
        self, 
        branch_name: str, 
        repo_url: str
    ) -> subprocess.CompletedProcess:
        try:
            result = self.run_subprocess(f"git clone -b {branch_name} {repo_url}", self.work_dir).stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(exc.stderr)
        return result
    
    def git_add(
        self, 
        work_dir: str, 
        pattern: str = "."
    ) -> subprocess.CompletedProcess:
        try:
            result = self.run_subprocess("git add -v".split() + [pattern], work_dir)
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(exc.stderr)
        return result

    def git_commit(
        self, 
        work_dir: str, 
        commit_message: str = "commit files to CSGHub"
    ) -> subprocess.CompletedProcess:
        try:
            result = self.run_subprocess("git commit -v -m".split() + [commit_message], work_dir)
        except subprocess.CalledProcessError as exc:
            if len(exc.stderr) > 0:
                raise EnvironmentError(exc.stderr)
            else:
                raise EnvironmentError(exc.stdout)
        return result

    def git_push(
        self,
        work_dir: str,
    ) -> subprocess.CompletedProcess:
        try:
            result = self.run_subprocess("git push".split(), work_dir)
        except subprocess.CalledProcessError as exc:
            if len(exc.stderr) > 0:
                raise EnvironmentError(exc.stderr)
            else:
                raise EnvironmentError(exc.stdout)
        return result
    
    def commits_to_push(self, work_dir: Union[str, Path]) -> int:
        try:
            result = self.run_subprocess(f"git cherry -v", work_dir)
            return len(result.stdout.split("\n"))
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(exc.stderr)

    def run_subprocess(
        self,
        command: Union[str, List[str]],
        folder: Optional[Union[str, Path]] = None,
        check: bool = True,
        **kwargs,
        ) -> subprocess.CompletedProcess:
        if isinstance(command, str):
            command = command.split()

        if isinstance(folder, Path):
            folder = str(folder)

        return subprocess.run(
            command,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=check,
            encoding="utf-8",
            errors="replace",
            cwd=folder or os.getcwd(),
            **kwargs,
        )   
