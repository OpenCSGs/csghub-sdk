from pathlib import Path
from typing import List, Optional, Union

from pycsghub.cli_utils import get_csghub_api
from pycsghub.constants import DEFAULT_REVISION
from pycsghub.snapshot_download import snapshot_download


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
        quiet: Optional[bool] = False,
        dry_run: Optional[bool] = False,
        force_download: Optional[bool] = False,
        max_workers: Optional[int] = 8,
):
    return snapshot_download(
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
            quiet=quiet,
            dry_run=dry_run,
            force_download=force_download,
            max_workers=max_workers,
    )


def upload_files(
        repo_id: str,
        repo_type: str,
        repo_file: str,
        path_in_repo: Optional[str] = "",
        revision: Optional[str] = DEFAULT_REVISION,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        commit_message: Optional[str] = None,
):
    api = get_csghub_api(token=token, endpoint=endpoint)
    api.upload_file(
            path_or_fileobj=repo_file,
            path_in_repo=path_in_repo or Path(repo_file).name,
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            commit_message=commit_message,
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
        include: Optional[Union[List[str], str]] = None,
        exclude: Optional[Union[List[str], str]] = None,
        delete_patterns: Optional[Union[List[str], str]] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        create_pr: Optional[bool] = False,
        private: Optional[bool] = False,
        every: Optional[float] = None,
):
    api = get_csghub_api(token=token, endpoint=endpoint)
    api.upload_folder(
            repo_id=repo_id,
            folder_path=local_path,
            path_in_repo=path_in_repo,
            repo_type=repo_type,
            revision=revision,
            allow_patterns=include,
            ignore_patterns=exclude,
            delete_patterns=delete_patterns,
            commit_message=commit_message,
            commit_description=commit_description,
            create_pr=create_pr,
            parent_commit=None,
    )
