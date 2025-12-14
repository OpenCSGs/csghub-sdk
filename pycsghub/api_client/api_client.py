from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from huggingface_hub.utils import filter_repo_objects

from pycsghub.commit_ops import build_payload, CommitOperationAdd, CommitOperationDelete
from pycsghub.csghub_api import CsgHubApi
from pycsghub.file_download import file_download as csghub_file_download
from pycsghub.snapshot_download import snapshot_download as csghub_snapshot_download
from pycsghub.utils import get_endpoint, get_repo_info
from pycsghub.cmd import repo

class CsghubApi:
    def __init__(self, token: Optional[str] = None, endpoint: Optional[str] = None, user_name: Optional[str] = None):
        self._api = CsgHubApi(token=token, endpoint=endpoint)
        self._token = token
        self._endpoint = endpoint
        self._user_name = user_name
    
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
        # Adapt to csghub_file_download signature
        # Note: subfolder handling in csghub might be different, usually path in filename
        final_filename = f"{subfolder}/{filename}" if subfolder else filename
        
        # Extract dry_run/quiet/source from kwargs if present
        dry_run = kwargs.get('dry_run', False)
        quiet = kwargs.get('quiet', False)
        source = kwargs.get('source', None)
        
        return csghub_file_download(
            repo_id=repo_id,
            file_name=final_filename,
            revision=revision,
            repo_type=repo_type,
            cache_dir=cache_dir,
            local_dir=local_dir,
            local_files_only=local_files_only,
            headers=headers,
            endpoint=endpoint or self._endpoint,
            token=token or self._token,
            force_download=force_download,
            dry_run=dry_run,
            quiet=quiet,
            source=source
        )
    
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
        # Extra args for CSGHub compatibility or enhancements
        endpoint: Optional[str] = None,
        source: Optional[str] = None,
        quiet: Optional[bool] = False,
        dry_run: Optional[bool] = False,
        force_download: Optional[bool] = False,
    ):
        # Delegate to pycsghub.snapshot_download
        return csghub_snapshot_download(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            cache_dir=cache_dir,
            local_dir=local_dir,
            local_files_only=local_files_only,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
            endpoint=endpoint or self._endpoint,
            token=token or self._token,
            source=source,
            dry_run=dry_run,
            force_download=force_download,
            max_workers=max_workers,
            quiet=quiet
        )
    
    def create_repo(
        self,
        repo_id: str,
        repo_type: Optional[str] = None,
        exist_ok: bool = False,
        private: bool = False,
        **kwargs
    ):
        # Reusing Repository logic for creation
        from pycsghub.repository import Repository
        repo = Repository(
            repo_id=repo_id,
            upload_path="..",
            repo_type=repo_type,
            token=self._token,
            endpoint=self._endpoint,
            auto_create=False
        )
        try:
            repo.create_new_repo()
        except Exception:
            if not exist_ok:
                raise
        return repo
    
    def repo_info(
        self,
        repo_id: str,
        revision: Optional[str] = None,
        repo_type: Optional[str] = None,
        token: Optional[str] = None,
    ):
        return get_repo_info(
            repo_id=repo_id,
            revision=revision,
            repo_type=repo_type,
            token=token or self._token,
            endpoint=self._endpoint
        )
    
    def create_branch(
        self,
        repo_id: str,
        branch: str,
        repo_type: Optional[str] = None,
        exist_ok: bool = False
    ):
        try:
            # Reusing Repository logic until CsgHubApi supports create_branch directly or via new endpoint
            from pycsghub.repository import Repository
            repo = Repository(
                repo_id=repo_id,
                upload_path="..",
                repo_type=repo_type,
                branch_name=branch,
                token=self._token,
                endpoint=self._endpoint
            )
            return repo.create_new_branch()
        except Exception:
            if not exist_ok:
                raise
    
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
        return repo.upload_files(
            repo_id=repo_id,
            repo_type=repo_type,
            repo_file=path_or_fileobj,
            path_in_repo=path_in_repo,
            revision=revision,
            endpoint=self._endpoint,
            token=self._token,
        )
    
    def upload_folder(
        self,
        *,
        repo_id: str,
        folder_path: Union[str, Path],
        path_in_repo: Optional[str] = None,
        repo_type: Optional[str] = None,
        revision: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        delete_patterns: Optional[Union[List[str], str]] = None,
        create_pr: Optional[bool] = None,
        parent_commit: Optional[str] = None,
    ) -> dict:
        return repo.upload_folder(
            repo_id=repo_id, 
            repo_type=repo_type,
            local_path=folder_path,
            path_in_repo=path_in_repo,
            revision=revision,
            endpoint=self._endpoint,
            token=self._token,
            user_name=self._user_name,
        )
