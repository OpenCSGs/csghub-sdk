import logging
import os
import tempfile
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Dict, List, Optional, Union

from huggingface_hub.file_download import DryRunFileInfo
from huggingface_hub.utils import filter_repo_objects

from pycsghub import utils
from pycsghub.cache import ModelFileSystemCache
from pycsghub.constants import DEFAULT_REVISION, REPO_TYPE_MODEL, REPO_TYPES
from pycsghub.errors import NotSupportError
from pycsghub.file_download import http_get
from pycsghub.utils import get_cache_dir, get_endpoint, get_file_download_url, model_id_to_group_owner_name, \
    pack_repo_file_info

logger = logging.getLogger(__name__)


def snapshot_download(
        repo_id: str,
        *,
        repo_type: Optional[str] = None,
        revision: Optional[str] = DEFAULT_REVISION,
        cache_dir: Union[str, Path, None] = None,
        local_dir: Union[str, Path, None] = None,
        local_files_only: Optional[bool] = False,
        cookies: Optional[CookieJar] = None,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        headers: Optional[Dict[str, str]] = None,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        source: Optional[str] = None,
        dry_run: Optional[bool] = False,
        force_download: Optional[bool] = False,
        max_workers: Optional[int] = 8,
        quiet: Optional[bool] = False,
) -> str:
    if repo_type is None:
        repo_type = REPO_TYPE_MODEL
    if repo_type not in REPO_TYPES:
        raise ValueError(f"Invalid repo type: {repo_type}. Accepted repo types are: {str(REPO_TYPES)}")
    
    if cache_dir is None:
        cache_dir = get_cache_dir(repo_type=repo_type)
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)
    
    temporary_cache_dir = os.path.join(cache_dir, 'temp')
    os.makedirs(temporary_cache_dir, exist_ok=True)
    
    if local_dir is None:
        local_dir = os.getcwd()
    if isinstance(local_dir, Path):
        local_dir = str(local_dir)
    
    group_or_owner, name = model_id_to_group_owner_name(repo_id)
    # name = name.replace('.', '___')
    
    cache = ModelFileSystemCache(cache_dir, group_or_owner, name, local_dir=local_dir)
    
    if local_files_only:
        if len(cache.cached_files) == 0:
            raise ValueError(
                    'Cannot find the requested files in the cached path and outgoing'
                    ' traffic has been disabled. To enable model look-ups and downloads'
                    " online, set 'local_files_only' to False.")
        return cache.get_root_location()
    else:
        download_endpoint = get_endpoint(endpoint=endpoint)
        if source == 'xet':
            try:
                import xet_core  # type: ignore
            except Exception:
                raise NotSupportError("xet source requires xet-core library to be installed")
            return os.path.join(cache_dir, group_or_owner, name)
        # make headers
        # todo need to add cookies？
        repo_info = utils.get_repo_info(repo_id,
                                        repo_type=repo_type,
                                        revision=revision,
                                        token=token,
                                        endpoint=download_endpoint,
                                        source=source)
        
        assert repo_info.sha is not None, "Repo info returned from server must have a revision sha."
        assert repo_info.siblings is not None, "Repo info returned from server must have a siblings list."
        repo_files = list(
                filter_repo_objects(
                        items=[f.rfilename for f in repo_info.siblings],
                        allow_patterns=allow_patterns,
                        ignore_patterns=ignore_patterns,
                )
        )
        
        if dry_run:
            infos = []
            sizes = {}
            try:
                for s in getattr(repo_info, 'siblings', []) or []:
                    if hasattr(s, 'rfilename') and hasattr(s, 'size'):
                        sizes[s.rfilename] = getattr(s, 'size') or 0
            except Exception:
                pass
            for f in repo_files:
                infos.append(DryRunFileInfo(filename=f, file_size=sizes.get(f, 0), will_download=True))
            return infos
        
        with tempfile.TemporaryDirectory(dir=temporary_cache_dir) as temp_cache_dir:
            def _download_one(repo_file: str):
                repo_file_info = pack_repo_file_info(repo_file, revision)
                if not force_download and cache.exists(repo_file_info):
                    file_name = os.path.basename(repo_file_info['Path'])
                    logger.info(f"File {file_name} already in '{cache.get_root_location()}', skip downloading!")
                    return
                url = get_file_download_url(
                        model_id=repo_id,
                        file_path=repo_file,
                        repo_type=repo_type,
                        revision=revision,
                        endpoint=download_endpoint,
                        source=source)
                logger.debug(f"Downloading {repo_file} from {url}")
                http_get(
                        url=url,
                        local_dir=temp_cache_dir,
                        file_name=repo_file,
                        headers=headers,
                        cookies=cookies,
                        token=token,
                        quiet=quiet)
                temp_file = os.path.join(temp_cache_dir, repo_file)
                savedFile = cache.put_file(repo_file_info, temp_file)
                logger.info(f"Saved file to '{savedFile}'")
            
            if max_workers and max_workers > 1:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=max_workers) as ex:
                    for f in repo_files:
                        ex.submit(_download_one, f)
                ex.shutdown(wait=True)
            else:
                for f in repo_files:
                    _download_one(f)
        
        cache.save_model_version(revision_info={'Revision': revision})
        return os.path.join(cache.get_root_location())
