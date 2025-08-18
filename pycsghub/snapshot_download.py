import logging
import os
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Dict, Optional, Union, Callable, List
import threading

from huggingface_hub.utils import filter_repo_objects
from tqdm import tqdm

from pycsghub import utils
from pycsghub.cache import ModelFileSystemCache
from pycsghub.constants import DEFAULT_REVISION, REPO_TYPES
from pycsghub.constants import REPO_TYPE_MODEL
from pycsghub.file_download import http_get, MultiThreadDownloader
from pycsghub.utils import (get_cache_dir,
                            pack_repo_file_info,
                            get_endpoint)
from pycsghub.utils import (get_file_download_url,
                            model_id_to_group_owner_name,
                            get_model_temp_dir)

logger = logging.getLogger(__name__)


class DownloadProgressTracker:
    """Download progress tracker"""
    
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.current_downloaded = 0
        self.success_count = 0
        self.failed_count = 0
        self.successful_files = []
        self.remaining_files = []
        self.lock = threading.Lock()
    
    def update_progress(self, file_name: str, success: bool):
        """Update download progress"""
        with self.lock:
            self.current_downloaded += 1
            if success:
                self.success_count += 1
                self.successful_files.append(file_name)
            else:
                self.failed_count += 1
            
            if file_name in self.remaining_files:
                self.remaining_files.remove(file_name)
    
    def get_progress_info(self) -> Dict:
        """Get current progress information"""
        with self.lock:
            return {
                'total_files': self.total_files,
                'current_downloaded': self.current_downloaded,
                'success_count': self.success_count,
                'failed_count': self.failed_count,
                'successful_files': self.successful_files.copy(),
                'remaining_count': len(self.remaining_files),
                'remaining_files': self.remaining_files.copy()
            }
    
    def set_remaining_files(self, files: List[str]):
        """Set remaining file list"""
        with self.lock:
            self.remaining_files = files.copy()


def snapshot_download(
        repo_id: str,
        *,
        repo_type: Optional[str] = None,
        revision: Optional[str] = DEFAULT_REVISION,
        cache_dir: Union[str, Path, None] = None,
        local_dir: Union[str, Path, None] = None,
        local_files_only: Optional[bool] = False,
        cookies: Optional[CookieJar] = None,
        allow_patterns: Optional[str] = None,
        ignore_patterns: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        source: Optional[str] = None,
        verbose: bool = False,
        max_workers: int = 4,
        use_parallel: bool = True,
        progress_callback: Optional[Callable[[Dict], None]] = None,
) -> str:
    if repo_type is None:
        repo_type = REPO_TYPE_MODEL
    if repo_type not in REPO_TYPES:
        raise ValueError(f"Invalid repo type: {repo_type}. Accepted repo types are: {str(REPO_TYPES)}")

    # Convert string patterns to lists
    if allow_patterns and isinstance(allow_patterns, str):
        allow_patterns = [allow_patterns]
    if ignore_patterns and isinstance(ignore_patterns, str):
        ignore_patterns = [ignore_patterns]

    if verbose:
        print(f"[VERBOSE] Starting download for repo_id: {repo_id}")
        print(f"[VERBOSE] repo_type: {repo_type}")
        print(f"[VERBOSE] revision: {revision}")
        print(f"[VERBOSE] allow_patterns: {allow_patterns}")
        print(f"[VERBOSE] ignore_patterns: {ignore_patterns}")
        print(f"[VERBOSE] use_parallel: {use_parallel}")
        print(f"[VERBOSE] max_workers: {max_workers}")

    if cache_dir is None:
        cache_dir = get_cache_dir(repo_type=repo_type)
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)

    if isinstance(local_dir, Path):
        local_dir = str(local_dir)
    elif isinstance(local_dir, str):
        pass
    else:
        local_dir = str(Path.cwd() / repo_id)

    os.makedirs(local_dir, exist_ok=True)
    if verbose:
        print(f"[VERBOSE] Created/verified local_dir: {local_dir}")

    if verbose:
        print(f"[VERBOSE] cache_dir: {cache_dir}")
        print(f"[VERBOSE] local_dir: {local_dir}")

    group_or_owner, name = model_id_to_group_owner_name(repo_id)
    # name = name.replace('.', '___')

    if verbose:
        print(f"[VERBOSE] Parsed repo_id - owner: {group_or_owner}, name: {name}")

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
        if verbose:
            print(f"[VERBOSE] download_endpoint: {download_endpoint}")

        # make headers
        # todo need to add cookies?
        if verbose:
            print(f"[VERBOSE] Getting repository info...")

        repo_info = utils.get_repo_info(repo_id,
                                        repo_type=repo_type,
                                        revision=revision,
                                        token=token,
                                        endpoint=download_endpoint,
                                        source=source)

        assert repo_info.sha is not None, "Repo info returned from server must have a revision sha."
        assert repo_info.siblings is not None, "Repo info returned from server must have a siblings list."

        if verbose:
            print(f"[VERBOSE] Repository SHA: {repo_info.sha}")
            print(f"[VERBOSE] Total files in repository: {len(repo_info.siblings)}")
            print(f"[VERBOSE] All files in repository:")
            for sibling in repo_info.siblings:
                print(f"[VERBOSE]   - {sibling.rfilename}")

        repo_files = list(
            filter_repo_objects(
                items=[f.rfilename for f in repo_info.siblings],
                allow_patterns=allow_patterns,
                ignore_patterns=ignore_patterns,
            )
        )

        if verbose:
            print(f"[VERBOSE] Files after filtering: {len(repo_files)}")
            for file in repo_files:
                print(f"[VERBOSE]   - {file}")
        model_temp_dir = get_model_temp_dir(cache_dir, f"{group_or_owner}/{name}")

        if verbose:
            print(f"[VERBOSE] model_temp_dir: {model_temp_dir}")
            print(f"[VERBOSE] Starting download loop for {len(repo_files)} files...")

        if use_parallel:
            download_tasks = []
            files_to_download = []

            for repo_file in repo_files:
                if verbose:
                    print(f"[VERBOSE] Processing file: {repo_file}")

                repo_file_info = pack_repo_file_info(repo_file, revision)
                if cache.exists(repo_file_info):
                    file_name = os.path.basename(repo_file_info['Path'])
                    print(f"File {file_name} already in '{cache.get_root_location()}', skip downloading!")
                    if verbose:
                        print(f"[VERBOSE] File already exists, skipping download")
                    continue

                if verbose:
                    print(f"[VERBOSE] File does not exist, preparing download...")

                # get download url
                url = get_file_download_url(
                    model_id=repo_id,
                    file_path=repo_file,
                    repo_type=repo_type,
                    revision=revision,
                    endpoint=download_endpoint,
                    source=source)

                if verbose:
                    print(f"[VERBOSE] Download URL: {url}")

                download_tasks.append({
                    'url': url,
                    'file_path': os.path.join(model_temp_dir, repo_file),
                    'headers': headers,
                    'cookies': cookies,
                    'token': token,
                    'file_name': repo_file
                })
                files_to_download.append(repo_file)

            if download_tasks:
                logger.info(f"Start parallel downloading {len(download_tasks)} files, using {max_workers} threads")

                progress_tracker = DownloadProgressTracker(len(download_tasks))
                progress_tracker.set_remaining_files(files_to_download)

                downloader = MultiThreadDownloader(max_workers=max_workers)

                with tqdm(total=len(download_tasks), desc="Parallel downloading files", unit="file") as pbar:
                    results = downloader.download_files_parallel_with_progress(
                        download_tasks, pbar, progress_tracker, progress_callback)

                failed_files = []
                for file_name, success in results.items():
                    if success:
                        temp_file = os.path.join(model_temp_dir, file_name)
                        repo_file_info = pack_repo_file_info(file_name, revision)
                        savedFile = cache.put_file(repo_file_info, temp_file)
                        print(f"Saved file to '{savedFile}'")
                        if verbose:
                            print(f"[VERBOSE] File successfully saved to: {savedFile}")
                    else:
                        failed_files.append(file_name)
                        logger.error(f"File download failed: {file_name}")

                if failed_files:
                    logger.error(f"Some files download failed: {failed_files}")
                    raise Exception(f"Some files download failed, please check network connection or retry")
        else:
            files_to_download = []
            for repo_file in repo_files:
                repo_file_info = pack_repo_file_info(repo_file, revision)
                if not cache.exists(repo_file_info):
                    files_to_download.append(repo_file)
            
            progress_tracker = DownloadProgressTracker(len(files_to_download))
            progress_tracker.set_remaining_files(files_to_download)
            
            for repo_file in repo_files:
                if verbose:
                    print(f"[VERBOSE] Processing file: {repo_file}")

                repo_file_info = pack_repo_file_info(repo_file, revision)
                if cache.exists(repo_file_info):
                    file_name = os.path.basename(repo_file_info['Path'])
                    print(f"File {file_name} already in '{cache.get_root_location()}', skip downloading!")
                    if verbose:
                        print(f"[VERBOSE] File already exists, skipping download")
                    continue

                if verbose:
                    print(f"[VERBOSE] File does not exist, downloading...")

                # get download url
                url = get_file_download_url(
                    model_id=repo_id,
                    file_path=repo_file,
                    repo_type=repo_type,
                    revision=revision,
                    endpoint=download_endpoint,
                    source=source)

                if verbose:
                    print(f"[VERBOSE] Download URL: {url}")

                # todo support parallel download api
                if verbose:
                    print(f"[VERBOSE] Starting HTTP download...")

                try:
                    http_get(
                        url=url,
                        local_dir=model_temp_dir,
                        file_name=repo_file,
                        headers=headers,
                        cookies=cookies,
                        token=token)

                    # todo using hash to check file integrity
                    temp_file = os.path.join(model_temp_dir, repo_file)
                    if verbose:
                        print(f"[VERBOSE] Temp file path: {temp_file}")

                    savedFile = cache.put_file(repo_file_info, temp_file)
                    print(f"Saved file to '{savedFile}'")

                    if verbose:
                        print(f"[VERBOSE] File successfully saved to: {savedFile}")
                    
                    progress_tracker.update_progress(repo_file, True)
                    
                except Exception as e:
                    logger.error(f"File download failed: {repo_file} - {e}")
                    progress_tracker.update_progress(repo_file, False)
                
                if progress_callback:
                    progress_info = progress_tracker.get_progress_info()
                    progress_callback(progress_info)

        cache.save_model_version(revision_info={'Revision': revision})

        final_location = os.path.join(cache.get_root_location())
        if verbose:
            print(f"[VERBOSE] Download completed. Final location: {final_location}")

        return final_location
