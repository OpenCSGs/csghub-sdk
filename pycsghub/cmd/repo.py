from pycsghub.snapshot_download import snapshot_download
from pycsghub.file_upload import http_upload_file
from pathlib import Path
from typing import Optional, Union, List
from pycsghub.constants import DEFAULT_REVISION
import requests


def download(
    repo_id: str,
    repo_type: str,
    revision: Optional[str] = DEFAULT_REVISION,
    cache_dir: Union[str, Path, None] = None,
    endpoint: Optional[str] = None,
    token: Optional[str] = None,
    mirror: Optional[str] = None
):
    snapshot_download(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        cache_dir=cache_dir,
        endpoint=endpoint,
        token=token,
        mirror=mirror,
    )


def upload(
    repo_id: str,
    repo_type: str,
    repo_files: List[str],
    revision: Optional[str] = DEFAULT_REVISION,
    endpoint: Optional[str] = None,
    token: Optional[str] = None
):
    for item in repo_files:
        http_upload_file(
            repo_id=repo_id,
            repo_type=repo_type,
            file_path=item,
            revision=revision,
            endpoint=endpoint,
            token=token,
        )
