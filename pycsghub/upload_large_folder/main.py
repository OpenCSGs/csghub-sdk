import logging
import os
import signal
import threading
import time
from pathlib import Path
from typing import Optional, Union, List

from tqdm.auto import tqdm

from pycsghub.cmd.repo_types import RepoType
from pycsghub.constants import DEFAULT_REVISION
from pycsghub.constants import REPO_TYPE_MODEL, REPO_TYPE_DATASET, REPO_TYPE_SPACE
from pycsghub.csghub_api import CsgHubApi
from pycsghub.utils import get_endpoint
from .consts import DEFAULT_IGNORE_PATTERNS
from .local_folder import get_local_upload_paths, read_upload_metadata
from .path import filter_repo_objects
from .status import LargeUploadStatus
from .workers import _worker_job

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
    try:
        folder_path = Path(local_path).expanduser().resolve()
        if not folder_path.is_dir():
            raise ValueError(f"provided path '{local_path}' is not a directory")

        if repo_type not in [REPO_TYPE_MODEL, REPO_TYPE_DATASET, REPO_TYPE_SPACE]:
            raise ValueError(
                f"invalid repo type, must be one of {REPO_TYPE_MODEL} or {REPO_TYPE_DATASET} or {REPO_TYPE_SPACE}")

        api_endpoint = get_endpoint(endpoint=endpoint)

        if ignore_patterns is None:
            ignore_patterns = []
        elif isinstance(ignore_patterns, str):
            ignore_patterns = [ignore_patterns]
        ignore_patterns += DEFAULT_IGNORE_PATTERNS

        if num_workers is None:
            nb_cores = os.cpu_count() or 1
            num_workers = max(nb_cores - 2, 2)

        api = CsgHubApi()

        create_repo(api=api, repo_id=repo_id, repo_type=repo_type, revision=revision, endpoint=api_endpoint,
                    token=token)

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

        print(status.current_report())
        logging.info("large folder upload process is complete!")
    except KeyboardInterrupt:
        print("Terminated by Ctrl+C")
        os.kill(os.getpid(), signal.SIGTERM)


def create_repo(
        api: CsgHubApi,
        repo_id: str,
        repo_type: str,
        revision: str,
        endpoint: str,
        token: str,
):
    repoExist, branchExist = api.repo_branch_exists(
        repo_id=repo_id, repo_type=repo_type, revision=revision,
        endpoint=endpoint, token=token)

    if not repoExist:
        api.create_new_repo(
            repo_id=repo_id, repo_type=repo_type, revision=revision,
            endpoint=endpoint, token=token)
        logger.info(f"repo {repo_type} {repo_id} created")
        if revision == DEFAULT_REVISION:
            branchExist = True

    if not branchExist:
        api.create_new_branch(
            repo_id=repo_id, repo_type=repo_type, revision=revision,
            endpoint=endpoint, token=token)
