import logging
import traceback
import time
import copy
from typing import Optional, List, Tuple, Dict
from .status import LargeUploadStatus, WorkerJob, JOB_ITEM_T
from .consts import WAITING_TIME_IF_NO_TASKS
from .jobs import _determine_next_job
from .sha import sha_fileobj
from pycsghub.csghub_api import CsgHubApi
from .utils import unquote
from .consts import (
    REPO_REGULAR_TYPE, 
    REPO_LFS_TYPE, 
    COMMIT_ACTION_CREATE, 
    COMMIT_ACTION_UPDATE,
    KEY_MSG, MSG_OK,
    KEY_UPLOADID
)
from urllib.parse import urlparse, parse_qs
from .slices import slice_upload, slices_upload_complete, slices_upload_verify

logger = logging.getLogger(__name__)

def _worker_job(
    status: LargeUploadStatus,
    api: CsgHubApi,
    repo_id: str,
    repo_type: str,
    revision: str,
    endpoint: str,
    token: str,
):
    """
    Main process for a worker. The worker will perform tasks based on the priority list until all files are uploaded
    and committed. If no tasks are available, the worker will wait for 10 seconds before checking again.

    If a task fails for any reason, the item(s) are put back in the queue for another worker to pick up.
    """
    while True:
        next_job: Optional[Tuple[WorkerJob, List[JOB_ITEM_T]]] = None

        # Determine next task
        next_job = _determine_next_job(status)
        if next_job is None:
            return
        job, items = next_job
        logger.debug(f"next job: {job}")
        # Perform task
        if job == WorkerJob.SHA256:
            _execute_job_compute_sha256(items=items, status=status)
        elif job == WorkerJob.GET_UPLOAD_MODE:
            _execute_job_get_upload_model(
                items=items, status=status,
                api=api, endpoint=endpoint, token=token,
                repo_id=repo_id, repo_type=repo_type, revision=revision)
        elif job == WorkerJob.PREUPLOAD_LFS:
            _execute_job_pre_upload_lfs(
                items=items, status=status, 
                api=api, endpoint=endpoint, token=token,
                repo_id=repo_id, repo_type=repo_type, revision=revision)
        elif job == WorkerJob.UPLOADING_LFS:
            _execute_job_uploading_lfs(items=items, status=status)
        elif job == WorkerJob.COMMIT:
            _execute_job_commit(
                items=items, status=status, 
                api=api, endpoint=endpoint, token=token,
                repo_id=repo_id, repo_type=repo_type, revision=revision)
        elif job == WorkerJob.WAIT:
            _execute_job_waiting(status=status)

def _execute_job_compute_sha256(
    items: List[JOB_ITEM_T], 
    status: LargeUploadStatus,
):
    item = items[0]  # single item every time
    paths, metadata = item
    try:
        _compute_sha256(item)
        logger.debug(f"computing sha256 for {item[0].file_path} successfully")
        status.queue_get_upload_mode.put(item)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error(f"failed to compute {paths.file_path} sha256: {e}")
        traceback.format_exc()
        status.queue_sha256.put(item)

    with status.lock:
        status.nb_workers_sha256 -= 1

def _execute_job_get_upload_model(
    items: List[JOB_ITEM_T], 
    status: LargeUploadStatus,
    api: CsgHubApi,
    repo_id: str,
    repo_type: str,
    revision: str,
    endpoint: str,
    token: str,
):
    # A maximum of 50 files at a time
    try:
        _get_upload_mode(
            items, api=api, endpoint=endpoint, token=token,
            repo_id=repo_id, repo_type=repo_type, revision=revision)
        logger.info(f"get upload modes for {len(items)} items successfully")
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error(f"failed to get {len(items)} items upload mode: {e}")
        traceback.format_exc()

    # Items are either:
    # - dropped (if should_ignore)
    # - put in LFS queue (if LFS)
    # - put in commit queue (if regular)
    # - or put back (if error occurred).
    ignore_num = 0
    same_with_remote_num = 0
    for item in items:
        paths, metadata = item
        if metadata.should_ignore:
            ignore_num += 1
            continue
        if ((metadata.upload_mode == REPO_REGULAR_TYPE and metadata.sha1 == metadata.remote_oid) or
            (metadata.upload_mode == REPO_LFS_TYPE and metadata.sha256 == metadata.remote_oid)):
            metadata.is_uploaded = True
            metadata.is_committed = True
            metadata.save(paths)
            same_with_remote_num += 1
            continue
        if metadata.upload_mode == REPO_LFS_TYPE:
            status.queue_preupload_lfs.put(item)
        elif metadata.upload_mode == REPO_REGULAR_TYPE:
            status.queue_commit.put(item)
        else:
            status.queue_get_upload_mode.put(item)

    if ignore_num > 0:
        logger.info(f"ignored {ignore_num} files because of should_ignore is true from remote server")
    
    if same_with_remote_num > 0:
        logger.info(f"skipped {same_with_remote_num} files because they are identical to the remote server")
    
    with status.lock:
        status.nb_workers_get_upload_mode -= 1

def _execute_job_pre_upload_lfs(
    items: List[JOB_ITEM_T], 
    status: LargeUploadStatus,
    api: CsgHubApi,
    repo_id: str,
    repo_type: str,
    revision: str,
    endpoint: str,
    token: str,
):
    item = items[0]  # single item every time
    paths, metadata = item
    action = "preupload"
    try:
        if status.is_lfs_upload_completed(item):
            action = f"{action} check complete"
            _preupload_lfs_done(item=item, status=status)
            status.queue_commit.put(item)
        else:
            action = f"{action} fetch batch info"
            is_uploaded = _preupload_lfs(
                item=item, status=status,
                api=api, endpoint=endpoint, token=token,
                repo_id=repo_id, repo_type=repo_type, revision=revision)
            if is_uploaded:
                status.queue_commit.put(item)
            else:
                # keep in queue preupload
                status.queue_preupload_lfs.put(item)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error(f"failed to {action} lfs {paths.file_path}: {e}")
        traceback.format_exc()
        status.queue_preupload_lfs.put(item)

    with status.lock:
        status.nb_workers_preupload_lfs -= 1   

def _execute_job_uploading_lfs(
    items: List[JOB_ITEM_T], 
    status: LargeUploadStatus,
):
    item = items[0] # single item every time
    paths, metadata = item
    try:
        etag = _perform_lfs_slice_upload(item)
        status.append_lfs_uploaded_slice_id(paths.file_path, metadata.lfs_upload_part_index, etag)
        metadata.lfs_uploaded_ids = status.get_lfs_uploaded_slice_ids(paths.file_path)
        metadata.save(paths)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error(f"failed to preupload LFS {paths.file_path} slice {metadata.lfs_upload_part_index}/{metadata.lfs_upload_part_count}: {e}")
        traceback.format_exc()
        status.queue_uploading_lfs.put(item)
        
    with status.lock:
        status.nb_workers_uploading_lfs -= 1

def _execute_job_commit(
    items: List[JOB_ITEM_T],
    status: LargeUploadStatus,
    api: CsgHubApi,
    repo_id: str,
    repo_type: str,
    revision: str,
    endpoint: str,
    token: str,
):
    try:
        for item in items:
            status.compute_file_base64(item=item)
        
        _commit(items, api=api, endpoint=endpoint, token=token,
            repo_id=repo_id, repo_type=repo_type, revision=revision)
        logger.info(f"committed {len(items)} items")
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error(f"failed to commit: {e}")
        traceback.format_exc()
        for item in items:
            status.queue_commit.put(item)

    with status.lock:
        status.last_commit_attempt = time.time()
        status.nb_workers_commit -= 1

def _execute_job_waiting(
    status: LargeUploadStatus,
):
    logger.info(f"no tasks available, waiting for {WAITING_TIME_IF_NO_TASKS} seconds")
    time.sleep(WAITING_TIME_IF_NO_TASKS)
    with status.lock:
        status.nb_workers_waiting -= 1    

def _compute_sha256(item: JOB_ITEM_T) -> None:
    """Compute sha256 of a file and save it in metadata."""
    paths, metadata = item
    if metadata.sha256 is None:
        with paths.file_path.open("rb") as f:
             sha256, sha1 = sha_fileobj(fileobj=f, item=item)
             metadata.sha256 = sha256
             metadata.sha1 = sha1
             
    metadata.save(paths)

def _get_upload_mode(
    items: List[JOB_ITEM_T],
    api: CsgHubApi, 
    repo_id: str, 
    repo_type: str, 
    revision: str,
    endpoint: str,
    token: str,
) -> None:
    """Get upload mode for each file and update metadata.

    Also receive info if the file should be ignored.
    """
    payload: Dict = {
        "files": [
            {
                "path": paths.path_in_repo,
                "size": meta.size,
            }
            for paths, meta in items
        ]
    }
    modes_resp = api.fetch_upload_modes(
        payload=payload, endpoint=endpoint, token=token,
        repo_id=repo_id, repo_type=repo_type, revision=revision)
    
    if modes_resp["data"] is None or modes_resp["data"]["files"] is None:
        raise ValueError("no correct upload modes response found")
        
    files_modes = modes_resp["data"]["files"]
    if not isinstance(files_modes, list):
        raise ValueError("files is not list in upload modes response")
    
    if not files_modes and len(files_modes) != len(items):
        raise ValueError(f"requested {len(items)} files do not match {len(files_modes)} files in fetch upload modes response")

    remote_upload_modes: Dict[str, str] = {}
    remote_should_ignore: Dict[str, bool] = {}
    remote_file_oids: Dict[str, Optional[str]] = {}
    
    for file in files_modes:
        key = file["path"]
        if file["isDir"]:
            raise ValueError(f"cannot upload '{key}' - the path exists as a directory in the remote repository")
        remote_upload_modes[key] = file["uploadMode"]
        remote_should_ignore[key] = file["shouldIgnore"]
        remote_file_oids[key] = file["oid"]
    
    for item in items:
        paths, metadata = item
        metadata.upload_mode = remote_upload_modes[paths.path_in_repo]
        metadata.should_ignore = remote_should_ignore[paths.path_in_repo]
        metadata.remote_oid = None if remote_file_oids[paths.path_in_repo] == "" else remote_file_oids[paths.path_in_repo]
        metadata.save(paths)

def _preupload_lfs_done(
    item: JOB_ITEM_T,
    status: LargeUploadStatus,
):
    paths, metadata = item
    uploaded_ids = status.get_lfs_uploaded_slice_ids(paths.file_path)
    uploaded_ids_map = status.convert_uploaded_ids_to_map(uploaded_ids)
    slices_upload_complete(item=item, uploaded_ids_map=uploaded_ids_map)
    slices_upload_verify(item=item)
    metadata.is_uploaded = True
    metadata.save(paths)
    logger.info(f"LFS file {paths.file_path} - all {metadata.lfs_upload_part_count} slices uploaded successfully")

def _preupload_lfs(
    item: JOB_ITEM_T,
    status: LargeUploadStatus,
    api: CsgHubApi, 
    repo_id: str, 
    repo_type: str, 
    revision: str,
    endpoint: str,
    token: str,
) -> bool:
    """Preupload LFS file and update metadata."""
    paths, metadata = item
    
    payload: Dict = {
        "operation": "upload",
        "transfers": ["basic", "multipart"],
        "objects": [
            {
                "oid": metadata.sha256,
                "size": metadata.size,
            }
        ],
        "hash_algo": "sha256",
        "upload_id": metadata.lfs_upload_id,
    }
    if revision is not None:
        payload["ref"] = {"name": unquote(revision)}  # revision has been previously 'quoted'
        
    batch_resp = api.fetch_lfs_batch_info(
        payload=payload, endpoint=endpoint, token=token,
        repo_id=repo_id, repo_type=repo_type, revision=revision, local_file=paths.file_path,
        upload_id=metadata.lfs_upload_id)
    
    objects = batch_resp.get("objects", None)
    if not isinstance(objects, list) or len(objects) < 1:
        raise ValueError(f"LFS {paths.file_path} malformed batch response objects is not list from server: {batch_resp}")
    object = objects[0]
    
    search_key = "actions"
    if not isinstance(object, dict) or search_key not in object:
        raise ValueError(f"no slices batch {search_key} info found for response of file {paths.file_path} from server: {object}")
    object_actions = object[search_key]
    
    search_key = "upload"
    if not isinstance(object_actions, dict) or search_key not in object_actions:
        raise ValueError(f"no slices batch {search_key} info found for response of file {paths.file_path} from server: {object}")
    object_upload = object_actions[search_key]
    
    search_key = "verify"
    if not isinstance(object_actions, dict) or search_key not in object_actions:
        raise ValueError(f"no slices batch {search_key} info found for response of file {paths.file_path} from server: {object}")
    object_verify = object_actions[search_key]
    
    search_key = "header"
    if not isinstance(object_upload, dict) or search_key not in object_upload:
        raise ValueError(f"no slices batch {search_key} found for response of file {paths.file_path} from server: {object}")
    object_upload_header = object_upload[search_key]
    
    href_key = "href"
    if not isinstance(object_upload, dict) or search_key not in object_upload:
        raise ValueError(f"no slices batch merge address found for response of file {paths.file_path} from server: {object}") 
    
    if not isinstance(object_upload_header, Dict):
        raise ValueError(f"incorrect lfs {paths.file_path} slices upload address from server: {object}")
    
    chunk_size = object_upload_header.pop("chunk_size")
    if chunk_size is None:
        raise ValueError(f"no chunk size found for lfs slices upload of file {paths.file_path}")
    
    total_count = len(object_upload_header)
    metadata.lfs_upload_part_count = total_count
    metadata.lfs_upload_complete_url = object_upload[href_key]
    metadata.lfs_upload_verify = object_verify
    
    sorted_keys = sorted(object_upload_header.keys(), key=lambda x: int(x))
    parsed_url = urlparse(object_upload_header.get(sorted_keys[0]))
    query_params = parse_qs(parsed_url.query)
    metadata.lfs_upload_id = query_params.get(KEY_UPLOADID, [None])[0]
    
    uploaded_ids = status.get_lfs_uploaded_slice_ids(paths.file_path)
    existing_ids = status.convert_uploaded_ids_to_map(uploaded_ids)
    for _, key in enumerate(sorted_keys):
        if existing_ids.get(key) is not None:
            continue
        upload_url = object_upload_header.get(key)
        slice_metadata = copy.deepcopy(metadata)
        slice_metadata.lfs_upload_part_count = total_count
        slice_metadata.lfs_upload_part_index = int(key)
        slice_metadata.lfs_upload_part_url = upload_url
        slice_metadata.lfs_upload_chunk_size = int(chunk_size)
        item_slice = [paths, slice_metadata]
        status.queue_uploading_lfs.put(item_slice)
    logger.info(f"get LFS {paths.file_path} slices batch info successfully")
    return False

def _perform_lfs_slice_upload(item: JOB_ITEM_T):
    resp_header = slice_upload(item=item)
    logger.debug(f"slice upload response header: {resp_header}")
    # ('eTag', '"c681604308d0749e988746229fc16b25"')
    etag = resp_header.get("etag")
    if etag is None or etag == "":
        raise ValueError(f"invalid slice upload response header: {resp_header}, etag: {etag}")
    return etag.removeprefix('"').removesuffix('"')

def _commit(
    items: List[JOB_ITEM_T],
    api: CsgHubApi, 
    repo_id: str, 
    repo_type: str, 
    revision: str,
    endpoint: str,
    token: str,
) -> None:
    """Commit files to the repo."""
    commit_message="Add files using upload-large-folder tool"
    payload: Dict = {
        "message": commit_message,
        "files": [
            {
                "path": paths.path_in_repo,
                "action": COMMIT_ACTION_CREATE if meta.remote_oid is None else COMMIT_ACTION_UPDATE,
                "content": meta.content_base64,
            }
            for paths, meta in items
        ]
    }
    
    commit_resp = api.create_commit(
        payload=payload, endpoint=endpoint, token=token,
        repo_id=repo_id, repo_type=repo_type, revision=revision)
    
    if commit_resp[KEY_MSG] is None or commit_resp[KEY_MSG] != MSG_OK:
        raise ValueError(f"create commit response message {commit_resp} is not {MSG_OK}")
    
    for paths, metadata in items:
        metadata.is_committed = True
        metadata.save(paths)
