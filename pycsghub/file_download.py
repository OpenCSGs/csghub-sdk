import logging
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Dict, List, Optional, Union

import requests
from huggingface_hub.utils import filter_repo_objects
from tqdm import tqdm
from urllib3.util.retry import Retry

from pycsghub import utils
from pycsghub.cache import ModelFileSystemCache
from pycsghub.constants import DEFAULT_REVISION, REPO_TYPES
from pycsghub.constants import REPO_TYPE_MODEL
from pycsghub.errors import InvalidParameter
from pycsghub.utils import (get_cache_dir,
                            pack_repo_file_info,
                            get_endpoint,
                            build_csg_headers)
from pycsghub.utils import (get_file_download_url,
                            model_id_to_group_owner_name,
                            get_model_temp_dir)

# API constants
API_FILE_DOWNLOAD_RETRY_TIMES = 3
API_FILE_DOWNLOAD_TIMEOUT = 30

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def try_to_load_from_cache():
    pass


def cached_download():
    pass


def csg_hub_download():
    pass


def get_csg_hub_url():
    pass


class MultiThreadDownloader:
    """Multi-threaded downloader"""

    def __init__(self, max_workers=4, chunk_size=8192, retry_times=3, timeout=30):
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.retry_times = retry_times
        self.timeout = timeout
        self.lock = threading.Lock()

    def download_file_with_retry(self, url: str, file_path: str, headers: dict = None,
                                 cookies: CookieJar = None, token: str = None,
                                 file_name: str = None, progress_bar: tqdm = None) -> bool:
        """Download a single file with retry mechanism"""
        headers = headers or {}
        get_headers = build_csg_headers(token=token, headers=headers)

        for attempt in range(self.retry_times + 1):
            try:
                logger.info(
                    f"Start downloading file: {file_name or os.path.basename(file_path)} (attempt {attempt + 1}/{self.retry_times + 1})")

                temp_file_path = file_path + '.tmp'

                with open(temp_file_path, 'wb') as f:
                    response = requests.get(
                        url,
                        headers=get_headers,
                        stream=True,
                        cookies=cookies,
                        timeout=self.timeout
                    )
                    response.raise_for_status()

                    total_size = int(response.headers.get('content-length', 0))

                    if progress_bar:
                        progress_bar.total = total_size
                        progress_bar.set_description(f"Downloading {file_name or os.path.basename(file_path)}")

                    downloaded_size = 0
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if progress_bar:
                                progress_bar.update(len(chunk))

                if total_size > 0:
                    actual_size = os.path.getsize(temp_file_path)
                    if actual_size != total_size:
                        logger.warning(f"File size mismatch: expected {total_size}, actual {actual_size}")
                        if attempt < self.retry_times:
                            logger.info(f"Retry downloading...")
                            continue
                        else:
                            logger.error(f"File size verification failed, reached maximum retry count")
                            return False

                os.rename(temp_file_path, file_path)
                logger.info(f"File download successful: {file_path}")
                return True

            except requests.exceptions.RequestException as e:
                logger.error(f"Download failed (attempt {attempt + 1}/{self.retry_times + 1}): {e}")
                if attempt < self.retry_times:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"File download failed, reached maximum retry count: {file_name or os.path.basename(file_path)}")
                    return False
            except Exception as e:
                logger.error(f"Unknown error (attempt {attempt + 1}/{self.retry_times + 1}): {e}")
                if attempt < self.retry_times:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"File download failed, reached maximum retry count: {file_name or os.path.basename(file_path)}")
                    return False

        return False

    def download_files_parallel(self, download_tasks: List[Dict],
                                progress_bar: tqdm = None) -> Dict[str, bool]:
        """Download multiple files in parallel"""
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {}
            for task in download_tasks:
                future = executor.submit(
                    self.download_file_with_retry,
                    url=task['url'],
                    file_path=task['file_path'],
                    headers=task.get('headers'),
                    cookies=task.get('cookies'),
                    token=task.get('token'),
                    file_name=task.get('file_name'),
                    progress_bar=progress_bar
                )
                future_to_file[future] = task.get('file_name', os.path.basename(task['file_path']))

            # Collect results
            for future in as_completed(future_to_file):
                file_name = future_to_file[future]
                try:
                    success = future.result()
                    results[file_name] = success
                except Exception as e:
                    logger.error(f"Download task exception: {file_name} - {e}")
                    results[file_name] = False

        return results

    def download_files_parallel_with_progress(self, download_tasks: List[Dict],
                                            progress_bar: tqdm = None,
                                            progress_tracker=None,
                                            progress_callback=None) -> Dict[str, bool]:
        """Download multiple files in parallel, support progress callback"""
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {}
            for task in download_tasks:
                future = executor.submit(
                    self.download_file_with_retry,
                    url=task['url'],
                    file_path=task['file_path'],
                    headers=task.get('headers'),
                    cookies=task.get('cookies'),
                    token=task.get('token'),
                    file_name=task.get('file_name'),
                    progress_bar=progress_bar
                )
                future_to_file[future] = task.get('file_name', os.path.basename(task['file_path']))

            for future in as_completed(future_to_file):
                file_name = future_to_file[future]
                try:
                    success = future.result()
                    results[file_name] = success
                    
                    if progress_tracker:
                        progress_tracker.update_progress(file_name, success)
                        
                        if progress_callback:
                            progress_info = progress_tracker.get_progress_info()
                            progress_callback(progress_info)
                            
                except Exception as e:
                    logger.error(f"Download task exception: {file_name} - {e}")
                    results[file_name] = False
                    
                    if progress_tracker:
                        progress_tracker.update_progress(file_name, False)
                        
                        if progress_callback:
                            progress_info = progress_tracker.get_progress_info()
                            progress_callback(progress_info)

        return results


def file_download(
        repo_id: str,
        *,
        file_name: str = None,
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
        repo_type: Optional[str] = None,
        source: Optional[str] = None,
        max_workers: int = 4,
        use_parallel: bool = True,
) -> str:
    if cache_dir is None:
        cache_dir = get_cache_dir(repo_type=repo_type)
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)

    if local_dir is not None and isinstance(local_dir, Path):
        local_dir = str(local_dir)

    if file_name is None:
        raise InvalidParameter('file_name cannot be None, if you want to load single file from repo {}'.format(repo_id))

    group_or_owner, name = model_id_to_group_owner_name(repo_id)
    if os.name == 'nt':
        name = name.replace('.', '___')
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')

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
        # make headers
        # todo need to add cookies?
        repo_info = utils.get_repo_info(repo_id=repo_id,
                                        revision=revision,
                                        token=token,
                                        endpoint=download_endpoint,
                                        repo_type=repo_type,
                                        source=source)

        assert repo_info.sha is not None, "Repo info returned from server must have a revision sha."
        assert repo_info.siblings is not None, "Repo info returned from server must have a siblings list."
        model_files = list(
            filter_repo_objects(
                items=[f.rfilename for f in repo_info.siblings],
                allow_patterns=allow_patterns,
                ignore_patterns=ignore_patterns,
            )
        )
        if file_name not in model_files:
            raise InvalidParameter('file {} not in repo {}'.format(file_name, repo_id))

        model_temp_dir = get_model_temp_dir(cache_dir, f"{group_or_owner}/{name}")

        repo_file_info = pack_repo_file_info(file_name, revision)
        if not cache.exists(repo_file_info):
            file_name = os.path.basename(repo_file_info['Path'])
            # get download url
            url = get_file_download_url(
                model_id=repo_id,
                file_path=file_name,
                revision=revision,
                endpoint=download_endpoint,
                repo_type=repo_type,
                source=source)

            if use_parallel:
                downloader = MultiThreadDownloader(max_workers=max_workers)
                download_tasks = [{
                    'url': url,
                    'file_path': os.path.join(model_temp_dir, file_name),
                    'headers': headers,
                    'cookies': cookies,
                    'token': token,
                    'file_name': file_name
                }]

                with tqdm(total=1, desc=f"Downloading file", unit="file") as pbar:
                    results = downloader.download_files_parallel(download_tasks, pbar)

                if not results.get(file_name, False):
                    raise Exception(f"File download failed: {file_name}")
            else:
                http_get(
                    url=url,
                    local_dir=model_temp_dir,
                    file_name=file_name,
                    headers=headers,
                    cookies=cookies,
                    token=token)

            # todo using hash to check file integrity
            temp_file = os.path.join(model_temp_dir, file_name)
            cache.put_file(repo_file_info, temp_file)
            print(f"Saved file to '{temp_file}'")
        else:
            print(f'File {file_name} already in {cache.get_root_location()}, skip downloading!')
        cache.save_model_version(revision_info={'Revision': revision})
        return os.path.join(cache.get_root_location(), file_name)


def snapshot_download_parallel(
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
) -> str:
    """Download snapshot of the entire repository in parallel"""
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
        print(f"[VERBOSE] Starting parallel download for repo_id: {repo_id}")
        print(f"[VERBOSE] repo_type: {repo_type}")
        print(f"[VERBOSE] revision: {revision}")
        print(f"[VERBOSE] allow_patterns: {allow_patterns}")
        print(f"[VERBOSE] ignore_patterns: {ignore_patterns}")

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
        # todo need to add cookies？
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
            print(f"[VERBOSE] Starting parallel download for {len(repo_files)} files...")

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

            # Prepare download tasks
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
            if use_parallel:
                downloader = MultiThreadDownloader(max_workers=max_workers)

                with tqdm(total=len(download_tasks), desc="Parallel downloading files", unit="file") as pbar:
                    results = downloader.download_files_parallel(download_tasks, pbar)

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
                for repo_file in files_to_download:
                    if verbose:
                        print(f"[VERBOSE] Starting HTTP download for {repo_file}...")

                    url = get_file_download_url(
                        model_id=repo_id,
                        file_path=repo_file,
                        repo_type=repo_type,
                        revision=revision,
                        endpoint=download_endpoint,
                        source=source)

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

                    repo_file_info = pack_repo_file_info(repo_file, revision)
                    savedFile = cache.put_file(repo_file_info, temp_file)
                    print(f"Saved file to '{savedFile}'")

                    if verbose:
                        print(f"[VERBOSE] File successfully saved to: {savedFile}")

        cache.save_model_version(revision_info={'Revision': revision})

        final_location = os.path.join(cache.get_root_location())
        if verbose:
            print(f"[VERBOSE] Download completed. Final location: {final_location}")

        return final_location


def http_get(*,
             url: str,
             local_dir: str,
             file_name: str,
             headers: dict = None,
             cookies: CookieJar = None,
             token: str = None) -> None:
    '''
    download core API，using python request to download file to local cache dirs
    :param token: csghub token
    :param url: url to download
    :param local_dir: local dir to download
    :param file_name: file name to download
    :param headers: http headers
    :param cookies: http cookies
    :return: None
    '''
    tempfile_mgr = partial(tempfile.NamedTemporaryFile, mode='wb', dir=local_dir, delete=False)
    get_headers = build_csg_headers(token=token, headers=headers)
    total_content_length = 0
    with tempfile_mgr() as temp_file:
        # retry sleep 0.5s, 1s, 2s, 4s
        retry = Retry(total=API_FILE_DOWNLOAD_RETRY_TIMES, backoff_factor=1, allowed_methods=['GET'])
        while True:
            try:
                downloaded_size = temp_file.tell()
                if downloaded_size > 0:
                    get_headers['Range'] = 'bytes=%d-' % downloaded_size
                r = requests.get(url, headers=get_headers, stream=True,
                                 cookies=cookies, timeout=API_FILE_DOWNLOAD_TIMEOUT)
                r.raise_for_status()
                accept_ranges = r.headers.get('Accept-Ranges')
                content_length = r.headers.get('Content-Length')
                if content_length:
                    total_content_length = int(content_length)
                if downloaded_size > 0 and accept_ranges != 'bytes':
                    # server doesn't support range requests, restart download
                    temp_file.seek(0)
                    temp_file.truncate()
                    downloaded_size = 0
                    total_content_length = 0
                    get_headers.pop('Range', None)
                    r = requests.get(url, headers=get_headers, stream=True,
                                     cookies=cookies, timeout=API_FILE_DOWNLOAD_TIMEOUT)
                    r.raise_for_status()
                    content_length = r.headers.get('Content-Length')
                    if content_length:
                        total_content_length = int(content_length)
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                break
            except requests.exceptions.RequestException as e:
                print(f"Download failed: {e}")
                if temp_file.tell() == 0:
                    raise e
                else:
                    # partial download, continue
                    continue
        temp_file.flush()
        temp_file.close()
        # move temp file to final location
        final_file = os.path.join(local_dir, file_name)
        os.rename(temp_file.name, final_file)
        print(f"Downloaded {file_name} to {final_file}")
        if total_content_length > 0:
            actual_size = os.path.getsize(final_file)
            if actual_size != total_content_length:
                print(
                    f"Warning: Downloaded file size ({actual_size}) doesn't match expected size ({total_content_length})")


if __name__ == '__main__':
    token = "your_access_token"

    url = "https://hub.opencsg.com/api/v1/models/wayne0019/lwfmodel/resolve/lfsfile.bin"
    local_dir = '/home/test/'
    file_name = 'test.txt'
    headers = None
    cookies = None
    http_get(url=url,
             token=token,
             local_dir=local_dir,
             file_name=file_name,
             headers=headers,
             cookies=cookies)
