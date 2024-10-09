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
from pycsghub.constants import GIT_ATTRIBUTES_CONTENT, REPO_TYPE_DATASET, REPO_TYPE_SPACE, REPO_TYPE_CODE
from pycsghub.utils import (build_csg_headers,
                            model_id_to_group_owner_name,
                            get_endpoint)

class Repository:
    def __init__(
        self,
        repo_id: str,
        upload_path: str,
        branch_name: Optional[str] = "main",
        work_dir: Optional[str] = "/tmp/csg",
        user_name: Optional[str] = "",
        token: Optional[str] = "",
        license: Optional[str] = "apache-2.0",
        nickname: Optional[str] = "",
        description: Optional[str] = "",
        repo_type: Optional[str] = None,
        endpoint: Optional[str] = None,
        auto_create: Optional[bool] = True,
        copy_files: Optional[bool] = True,
    ):    
        self.repo_id = repo_id
        self.upload_path = upload_path
        self.branch_name = branch_name
        self.work_dir = work_dir
        self.user_name = user_name
        self.token = token
        self.license = license
        self.nickname = nickname
        self.description = description
        self.repo_type = repo_type
        self.endpoint = endpoint
        self.auto_create = auto_create
        self.copy_files = copy_files
        self.repo_url_prefix = self.get_url_prefix()
        self.namespace, self.name = model_id_to_group_owner_name(model_id=self.repo_id)
        self.repo_dir = os.path.join(self.work_dir, self.name)
        
    def get_url_prefix(self):
        if self.repo_type == REPO_TYPE_DATASET:
            return "datasets"
        if self.repo_type == REPO_TYPE_SPACE:
            return "spaces"
        if self.repo_type == REPO_TYPE_CODE:
            return "codes"
        else:
            return "models"
    
    def upload(self) -> None:
        if not os.path.exists(self.upload_path):
           raise ValueError("upload path does not exist")
       
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir, exist_ok=True)
        
        if self.auto_create:
            self.auto_create_repo_and_branch()
        
        if os.path.exists(self.repo_dir):
            shutil.rmtree(self.repo_dir)
            
        repo_url = self.generate_repo_clone_url()
        self.git_clone(branch_name=self.branch_name, repo_url=repo_url)
        
        git_cmd_workdir = self.copy_repo_files()
        
        self.git_add(work_dir=git_cmd_workdir)
        self.git_commit(work_dir=git_cmd_workdir)
        number_of_commits = self.commits_to_push(work_dir=git_cmd_workdir)
        if number_of_commits > 1:
            self.git_push(work_dir=git_cmd_workdir)

    def copy_repo_files(self):
        from_path = ""
        git_cmd_workdir = ""
        if self.copy_files or os.path.isfile(self.upload_path):
            from_path = self.upload_path
            git_cmd_workdir = self.repo_dir
            
            for item in os.listdir(git_cmd_workdir):
                item_path = os.path.join(git_cmd_workdir, item)
                if item != '.git' and item != '.gitattributes':
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        
            if os.path.isfile(self.upload_path):
                shutil.copyfile(self.upload_path, git_cmd_workdir)
            else:
                shutil.copytree(from_path, git_cmd_workdir, dirs_exist_ok=True)
        else:
            from_path = self.repo_dir
            git_cmd_workdir = self.upload_path
            
            for item in os.listdir(from_path):
                item_path = os.path.join(from_path, item)
                if item == '.git' or item == '.gitattributes':
                    if os.path.isdir(item_path):
                        shutil.copytree(item_path, os.path.join(git_cmd_workdir, item), dirs_exist_ok=True)
                    else:
                        shutil.copy2(item_path, git_cmd_workdir)
        
        return git_cmd_workdir     

    def auto_create_repo_and_branch(self):
        repoExist, branchExist = self.repo_exists()
        if not repoExist:
            response = self.create_new_repo()
            if response.status_code != 200:
                err_msg = f"fail to create new repo for {self.repo_id} with http status code '{response.status_code}' and message '{response.text}'"
                raise ValueError(err_msg)
            repoExist, branchExist = self.repo_exists()
        
        if not branchExist:
            response = self.create_new_branch()
            if response.status_code != 200:
                err_msg = f"fail to request new branch {self.branch_name} for {self.repo_id} with status code '{response.status_code}' and message {response.text}"
                raise ValueError(err_msg)
            branch_res = response.json()
            if branch_res["msg"] != "OK":
                raise ValueError(f"fail to create new branch {self.branch_name} for {self.repo_id}")

    def repo_exists(self):
        action_endpoint = get_endpoint(endpoint=self.endpoint)
        url = f"{action_endpoint}/api/v1/{self.repo_url_prefix}/{self.repo_id}/branches"
        headers = build_csg_headers(token=self.token, headers={
            "Content-Type": "application/json"
        })
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return False, False
        
        response.raise_for_status()
        
        jsonRes = response.json()
        if jsonRes["msg"] != "OK":
            return True, False

        branches = jsonRes["data"]
        for b in branches:
            if b["name"] == self.branch_name:
                return True, True
        
        return True, False
        
    def create_new_branch(self):
        action_endpoint = get_endpoint(endpoint=self.endpoint)
        url = f"{action_endpoint}/api/v1/{self.repo_url_prefix}/{self.repo_id}/raw/.gitattributes"
        
        GIT_ATTRIBUTES_CONTENT_BASE64 = base64.b64encode(GIT_ATTRIBUTES_CONTENT.encode()).decode()

        data = {
            "message": f"create new branch {self.branch_name} by data flow",
            "new_branch": self.branch_name,
            "content": GIT_ATTRIBUTES_CONTENT_BASE64
        }
        
        headers = build_csg_headers(token=self.token, headers={
            "Content-Type": "application/json"
        })
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response

    def create_new_repo(self):
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
            result = self.run_subprocess(
                command=f"git clone -b {branch_name} {repo_url}", 
                folder=self.work_dir,
                check=True,
                env={"GIT_LFS_SKIP_SMUDGE": "1"}
            ).stdout.strip()
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
