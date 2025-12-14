from typing import Optional, Protocol, Union, Dict, Any
from pathlib import Path
from typing import List


class HubApi(Protocol):
    def create_repo(
        self,
        repo_id: str,
        repo_type: Optional[str] = None,
        exist_ok: bool = False,
        private: bool = False,
        **kwargs
    ) -> str:
        ...

    def create_branch(
        self,
        repo_id: str,
        branch: str,
        repo_type: Optional[str] = None,
        exist_ok: bool = False
    ) -> None:
        ...

    def repo_info(
        self,
        repo_id: str,
        revision: Optional[str] = None,
        repo_type: Optional[str] = None,
        token: Optional[str] = None,
    ):
        ...

    def upload_file(
        self,
        *,
        path_or_fileobj: Union[str, Path, bytes],
        path_in_repo: str,
        repo_id: str,
        repo_type: Optional[str] = None,
        revision: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        create_pr: Optional[bool] = None,
        parent_commit: Optional[str] = None,
    ) -> dict:
        ...

    def upload_folder(
        self,
        *,
        repo_id: str,
        folder_path: Union[str, Path],
        path_in_repo: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        repo_type: Optional[str] = None,
        revision: Optional[str] = None,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        delete_patterns: Optional[Union[List[str], str]] = None,
        create_pr: Optional[bool] = None,
        parent_commit: Optional[str] = None,
    ) -> dict:
        ...

    def snapshot_download(
        self,
        repo_id: str,
        revision: Optional[str] = None,
        repo_type: Optional[str] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        local_dir: Optional[Union[str, Path]] = None,
        library_name: Optional[str] = None,
        library_version: Optional[str] = None,
        user_agent: Optional[Union[Dict, str]] = None,
        proxies: Optional[Dict] = None,
        etag_timeout: float = 10,
        resume_download: bool = False,
        token: Optional[Union[bool, str]] = None,
        local_files_only: bool = False,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        max_workers: int = 8,
        tqdm_class: Optional[Any] = None,
        **kwargs
    ) -> Union[str, Path]:
        ...

    def hf_hub_download(
        self,
        repo_id: str,
        filename: str,
        subfolder: Optional[str] = None,
        repo_type: Optional[str] = None,
        revision: Optional[str] = None,
        library_name: Optional[str] = None,
        library_version: Optional[str] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        local_dir: Optional[Union[str, Path]] = None,
        user_agent: Optional[Union[Dict, str]] = None,
        force_download: bool = False,
        force_filename: Optional[str] = None,
        proxies: Optional[Dict] = None,
        etag_timeout: float = 10,
        resume_download: bool = False,
        token: Optional[Union[bool, str]] = None,
        local_files_only: bool = False,
        headers: Optional[Dict[str, str]] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ) -> Union[str, Path]:
        ...
