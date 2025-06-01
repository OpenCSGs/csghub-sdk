import os
import logging
import threading
import time
import sys
from pathlib import Path
from tqdm.auto import tqdm
from typing import Optional, Union, List, Tuple
from pycsghub.cmd.repo_types import RepoType
from pycsghub.constants import REPO_TYPES
from pycsghub.utils import get_endpoint
from .path import filter_repo_objects
from .local_folder import get_local_upload_paths, read_upload_metadata
from .workers import _worker_job
from .status import LargeUploadStatus
from .consts import DEFAULT_IGNORE_PATTERNS
from pycsghub.csghub_api import CsgHubApi

logger = logging.getLogger(__name__)

def upload_large_folder_internal(
    repo_id: str,
    local_path: str,
    repo_type: RepoType,
    revision: str,
    endpoint: str,
    token: str,
    allow_patterns: Optional[Union[List[str], str]],
    ignore_patterns: Optional[Union[List[str], str]],
    num_workers: Optional[int],
    print_report: bool,
    print_report_every: int,
):
    folder_path = Path(local_path).expanduser().resolve()
    if not folder_path.is_dir():
        raise ValueError(f"provided path '{local_path}' is not a directory")
    
    if repo_type not in REPO_TYPES:
        raise ValueError(f"invalid repo type, must be one of {REPO_TYPES}")
    
    api_endpoint = get_endpoint(endpoint=endpoint)

    if ignore_patterns is None:
        ignore_patterns = []
    elif isinstance(ignore_patterns, str):
        ignore_patterns = [ignore_patterns]
    ignore_patterns += DEFAULT_IGNORE_PATTERNS
    
    if num_workers is None:
        nb_cores = os.cpu_count() or 1
        num_workers = max(nb_cores - 2, 2)
    
    filtered_paths_list = filter_repo_objects(
        (path.relative_to(folder_path).as_posix() for path in folder_path.glob("**/*") if path.is_file()),
        allow_patterns=allow_patterns,
        ignore_patterns=ignore_patterns,
    )
    
    paths_list = [get_local_upload_paths(folder_path, relpath) for relpath in filtered_paths_list]
    
    items = [
        (paths, read_upload_metadata(folder_path, paths.path_in_repo))
        for paths in tqdm(paths_list, desc=f"recovering from cache metadata from {folder_path}/.cache")
    ]

    logger.info(f"starting {num_workers} worker threads for upload tasks")
    status = LargeUploadStatus(items)
    api = CsgHubApi()
    threads = [
        threading.Thread(
            target=_worker_job,
            kwargs={
                "status": status,
                "api": api,
                "repo_id": repo_id,
                "repo_type": repo_type,
                "revision": revision,
                "endpoint": api_endpoint,
                "token": token,
            },
        )
        for _ in range(num_workers)
    ]
    
    for thread in threads:
        thread.start()

    if print_report:
        print('\n' + status.current_report())
    last_report_ts = time.time()
    while True:
        time.sleep(1)
        if time.time() - last_report_ts >= print_report_every:
            if print_report:
                print(status.current_report())
            last_report_ts = time.time()
        if status.is_done():
            logging.info("all files are done and exiting main loop")
            break

    for thread in threads:
        thread.join()
        
    if print_report:
        print(status.current_report())
    logging.info("large folder upload process is complete!")
