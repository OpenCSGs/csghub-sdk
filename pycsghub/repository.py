import base64
import os
import re
import shutil
import subprocess
import tempfile
import traceback
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

import requests

from pycsghub.constants import (GIT_ATTRIBUTES_CONTENT,
                                OPERATION_ACTION_GIT,
                                REPO_TYPE_DATASET,
                                REPO_TYPE_SPACE,
                                REPO_TYPE_CODE)
from pycsghub.constants import (GIT_HIDDEN_DIR)
from pycsghub.utils import (build_csg_headers,
                            model_id_to_group_owner_name,
                            get_endpoint)


def ignore_folders(folder, contents):
    ignored = []
    exclude_list = [GIT_HIDDEN_DIR]
    for item in contents:
        if item in exclude_list:
            ignored.append(item)
    return ignored


class Repository:
    def __init__(
            self,
            repo_id: str,
            upload_path: str,
            path_in_repo: Optional[str] = "",
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
            verbose: bool = False,
    ):
        self.repo_id = repo_id
        self.upload_path = upload_path
        self.path_in_repo = path_in_repo
        self.branch_name = branch_name
        if os.name == "nt":
            self.work_dir = os.path.join(tempfile.gettempdir(), "csg")
        else:
            self.work_dir = work_dir
        self.user_name = user_name
        self.token = token
        self.license = license
        self.nickname = nickname
        self.description = description
        self.repo_type = repo_type
        self.endpoint = endpoint
        self.auto_create = auto_create
        self.verbose = verbose
        self.repo_url_prefix = self.get_url_prefix()
        self.namespace, self.name = model_id_to_group_owner_name(model_id=self.repo_id)
        self.repo_dir = os.path.join(self.work_dir, self.name)
        self.user_name = self.user_name if self.user_name else self.namespace

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
        if self.verbose:
            print(f"[DEBUG] Starting upload process...")
            print(f"[DEBUG] Upload path: {self.upload_path}")
            print(f"[DEBUG] Work dir: {self.work_dir}")
            print(f"[DEBUG] Repo ID: {self.repo_id}")
            print(f"[DEBUG] Repo type: {self.repo_type}")
        
        if not os.path.exists(self.upload_path):
            raise ValueError("upload path does not exist")

        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir, exist_ok=True)

        if self.auto_create:
            if self.verbose:
                print(f"[DEBUG] Auto-creating repo and branch...")
            self.auto_create_repo_and_branch()

        repo_url = self.generate_repo_clone_url()
        
        if self.verbose:
            print(f"[DEBUG] Repo URL: {repo_url}")

        if os.path.exists(self.repo_dir):
            try:
                if self.verbose:
                    print(f"[DEBUG] Repository exists, pulling latest changes...")
                self.git_pull(work_dir=self.repo_dir)
            except Exception as e:
                if self.verbose:
                    print(f"[DEBUG] Pull failed, removing and re-cloning: {str(e)}")
                print(f"Update repository failed, re-cloning: {str(e)}")
                try:
                    shutil.rmtree(self.repo_dir)
                except PermissionError as e:
                    print(traceback.format_exc())
                    raise Exception("permission denied,please run this program with administrator privileges")
                self.git_clone(branch_name=self.branch_name, repo_url=repo_url)
        else:
            if self.verbose:
                print(f"[DEBUG] Repository doesn't exist, cloning...")
            self.git_clone(branch_name=self.branch_name, repo_url=repo_url)

        if self.verbose:
            print(f"[DEBUG] Copying files to repository...")
        git_cmd_workdir = self.copy_repo_files()

        if self.verbose:
            print(f"[DEBUG] Tracking large files...")
        self.track_large_files(work_dir=git_cmd_workdir)
        
        if self.verbose:
            print(f"[DEBUG] Adding files to git...")
        self.git_add(work_dir=git_cmd_workdir)
        
        if self.verbose:
            print(f"[DEBUG] Committing changes...")
        self.git_commit(work_dir=git_cmd_workdir)
        
        number_of_commits = self.commits_to_push(work_dir=git_cmd_workdir)
        if self.verbose:
            print(f"[DEBUG] Commits to push: {number_of_commits}")
        
        if number_of_commits > 1:
            if self.verbose:
                print(f"[DEBUG] Pushing changes to remote...")
            self.git_push(work_dir=git_cmd_workdir)

    def copy_repo_files(self):
        """Copy files to repository directory, optimized version"""
        from_path = self.upload_path
        git_cmd_workdir = self.repo_dir

        path_suffix = f"{self.path_in_repo.strip('/')}/" if self.path_in_repo else ""
        path_suffix = re.sub(r'^\./', '', path_suffix)

        try:
            destination_path = os.path.join(git_cmd_workdir, path_suffix)
            os.path.normpath(destination_path)
        except (OSError, ValueError) as e:
            print(f"Path encoding error: {e}")
            destination_path = os.path.join(git_cmd_workdir, "upload")

        if not os.path.exists(destination_path):
            os.makedirs(destination_path, exist_ok=True)

        if os.path.isfile(self.upload_path):
            try:
                filename = os.path.basename(self.upload_path)
                safe_filename = self._get_safe_filename(filename)
                destination_file_path = os.path.join(destination_path, safe_filename)
                shutil.copyfile(self.upload_path, destination_file_path)
            except (OSError, UnicodeError) as e:
                print(f"File copy failed: {e}")
                destination_file_path = os.path.join(destination_path, "uploaded_file")
                shutil.copyfile(self.upload_path, destination_file_path)
        else:
            try:
                shutil.copytree(from_path, destination_path, dirs_exist_ok=True, ignore=ignore_folders)
            except (OSError, UnicodeError) as e:
                print(f"Directory copy failed: {e}")
                self._copy_files_individually(from_path, destination_path)

        return git_cmd_workdir

    def _get_safe_filename(self, filename):
        """Get safe filename, handle encoding issues"""
        try:
            filename.encode('utf-8').decode('utf-8')
            return filename
        except UnicodeError:
            import hashlib
            safe_name = hashlib.md5(filename.encode('utf-8', errors='ignore')).hexdigest()
            ext = os.path.splitext(filename)[1]
            return f"file_{safe_name}{ext}"

    def _copy_files_individually(self, from_path, destination_path):
        """Copy files individually, handle encoding issues"""
        if not os.path.exists(from_path):
            return

        for item in os.listdir(from_path):
            try:
                source_item = os.path.join(from_path, item)
                dest_item = os.path.join(destination_path, self._get_safe_filename(item))

                if os.path.isfile(source_item):
                    shutil.copyfile(source_item, dest_item)
                elif os.path.isdir(source_item):
                    os.makedirs(dest_item, exist_ok=True)
                    self._copy_files_individually(source_item, dest_item)
            except (OSError, UnicodeError) as e:
                print(f"Skip file {item}: {e}")
                continue

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
            "message": f"create new branch {self.branch_name}",
            "new_branch": self.branch_name,
            "content": GIT_ATTRIBUTES_CONTENT_BASE64
        }

        headers = build_csg_headers(token=self.token, headers={
            "Content-Type": "application/json"
        })
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            print(f"create branch on {url} response: {response.text}")
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
        if response.status_code != 200:
            print(f"create repo on {url} response: {response.text}")
        response.raise_for_status()
        return response

    def generate_repo_clone_url(self) -> str:
        clone_endpoint = get_endpoint(endpoint=self.endpoint, operation=OPERATION_ACTION_GIT)
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
            env = os.environ.copy()
            env.update({"GIT_LFS_SKIP_SMUDGE": "1"})
            if os.name == "nt":
                try:
                    self.run_subprocess("git config --global core.quotepath false".split(), folder=self.work_dir,
                                        check=False)
                except:
                    pass  # ignore configuration error, continue execution

            result = self.run_subprocess(
                command=f"git clone -b {branch_name} {repo_url}",
                folder=self.work_dir,
                check=True,
                env=env
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
                err_str = exc.stdout
                if "nothing to commit, working tree clean" in err_str:
                    print(err_str)
                    exit()
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

    def git_pull(
            self,
            work_dir: str,
    ) -> subprocess.CompletedProcess:
        """Update repository to the latest version"""
        try:
            result = self.run_subprocess("git pull".split(), work_dir)
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

    def track_large_files(self, work_dir: str, pattern: str = ".") -> List[str]:
        files_to_be_tracked_with_lfs = []

        deleted_files = self.list_deleted_files(work_dir=work_dir)

        for filename in self.list_files_to_be_staged(work_dir=work_dir, pattern=pattern):
            if filename in deleted_files:
                continue

            path_to_file = os.path.join(os.getcwd(), work_dir, filename)
            size_in_mb = os.path.getsize(path_to_file) / (1024 * 1024)

            if size_in_mb >= 1 and not self.is_tracked_with_lfs(filename=path_to_file) and not self.is_git_ignored(
                    filename=path_to_file):
                self.lfs_track(work_dir=work_dir, patterns=filename)
                files_to_be_tracked_with_lfs.append(filename)

        self.lfs_untrack(work_dir=work_dir, patterns=deleted_files)

        return files_to_be_tracked_with_lfs

    def list_files_to_be_staged(self, work_dir: str, pattern: str = ".") -> List[str]:
        try:
            try:
                self.run_subprocess("git config --global core.quotepath false".split(), work_dir)
            except subprocess.CalledProcessError:
                try:
                    self.run_subprocess("git config core.quotepath false".split(), work_dir)
                except subprocess.CalledProcessError:
                    pass

            p = self.run_subprocess("git ls-files --exclude-standard -mo".split() + [pattern], work_dir)
            if len(p.stdout.strip()):
                files = p.stdout.strip().split("\n")
            else:
                files = []
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(exc.stderr)

        return files

    def list_deleted_files(self, work_dir: str) -> List[str]:
        try:
            git_status = self.run_subprocess("git status -s", work_dir).stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(exc.stderr)

        if len(git_status) == 0:
            return []

        modified_files_statuses = [status.strip() for status in git_status.split("\n")]
        deleted_files_statuses = [status for status in modified_files_statuses if "D" in status.split()[0]]
        deleted_files = [status.split()[-1].strip() for status in deleted_files_statuses]
        return deleted_files

    def lfs_track(self, work_dir: str, patterns: Union[str, List[str]], filename: bool = False):
        if isinstance(patterns, str):
            patterns = [patterns]
        try:
            for pattern in patterns:
                self.run_subprocess(
                    f"git lfs track {'--filename' if filename else ''} {pattern}",
                    work_dir,
                )
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(exc.stderr)

    def lfs_untrack(self, work_dir: str, patterns: Union[str, List[str]]):
        if isinstance(patterns, str):
            patterns = [patterns]
        try:
            for pattern in patterns:
                self.run_subprocess("git lfs untrack".split() + [pattern], work_dir)
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(exc.stderr)

    def is_tracked_with_lfs(self, filename: Union[str, Path]) -> bool:
        folder = Path(filename).parent
        filename = Path(filename).name

        try:
            p = self.run_subprocess("git check-attr -a".split() + [filename], folder)
            attributes = p.stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise OSError(exc.stderr)

        if len(attributes) == 0:
            return False

        found_lfs_tag = {"diff": False, "merge": False, "filter": False}

        for attribute in attributes.split("\n"):
            for tag in found_lfs_tag.keys():
                if tag in attribute and "lfs" in attribute:
                    found_lfs_tag[tag] = True

        return all(found_lfs_tag.values())

    def is_git_ignored(self, filename: Union[str, Path]) -> bool:
        folder = Path(filename).parent
        filename = Path(filename).name

        try:
            p = self.run_subprocess("git check-ignore".split() + [filename], folder, check=False)
            is_ignored = not bool(p.returncode)
        except subprocess.CalledProcessError as exc:
            raise OSError(exc.stderr)

        return is_ignored

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
