from pycsghub.snapshot_download import snapshot_download
from pycsghub.file_upload import http_upload_file
from pathlib import Path
from typing import Optional, Union, List
from pycsghub.constants import DEFAULT_REVISION
from pycsghub.repository import Repository
from pycsghub.utils import get_token_to_send

def download(
        repo_id: str,
        repo_type: str,
        revision: Optional[str] = DEFAULT_REVISION,
        cache_dir: Union[str, Path, None] = None,
        local_dir: Union[str, Path, None] = None,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        source: str = None,
    ):
    snapshot_download(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        cache_dir=cache_dir,
        local_dir=local_dir,
        endpoint=endpoint, 
        token=token,
        allow_patterns=allow_patterns,
        ignore_patterns=ignore_patterns,
        source=source,
    )

def upload_files(
        repo_id: str,
        repo_type: str,
        repo_file: str,
        path_in_repo: Optional[str] = "",
        revision: Optional[str] = DEFAULT_REVISION,
        endpoint: Optional[str] = None,
        token: Optional[str] = None
    ):
    http_upload_file(
        repo_id=repo_id,
        repo_type=repo_type,
        file_path=repo_file,
        path_in_repo=path_in_repo,
        revision=revision,
        endpoint=endpoint,
        token=token,
    )

def upload_folder(
        repo_id: str,
        repo_type: str,
        local_path: str,
        path_in_repo: Optional[str] = "",
        work_dir: Optional[str] = "/tmp/csg",
        nickname: Optional[str] = "",
        description: Optional[str] = "",
        license: Optional[str] = "apache-2.0",
        revision: Optional[str] = DEFAULT_REVISION,
        endpoint: Optional[str] = None,
        user_name: Optional[str] = "",
        token: Optional[str] = None,
        auto_create: Optional[bool] = True,
    ):
    r = Repository(
        repo_id=repo_id,
        upload_path=local_path,
        path_in_repo=path_in_repo,
        work_dir=work_dir,
        repo_type=repo_type,
        nickname=nickname,
        description=description,
        license=license,
        branch_name=revision,
        endpoint=endpoint,
        user_name=user_name,
        token=get_token_to_send(token),
        auto_create=auto_create,
    )
    r.upload()
    