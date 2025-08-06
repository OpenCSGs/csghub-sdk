import logging
import queue
import time
from typing import List, Optional, Tuple

from .consts import WAITING_TIME_IF_NO_TASKS, MAX_NB_LFS_FILES_PER_COMMIT, MAX_NB_REGULAR_FILES_PER_COMMIT
from .status import LargeUploadStatus, WorkerJob, JOB_ITEM_T

logger = logging.getLogger(__name__)


def _determine_next_job(status: LargeUploadStatus) -> Optional[Tuple[WorkerJob, List[JOB_ITEM_T]]]:
    with status.lock:
        # Commit if more than 5 minutes since last commit attempt (and at least 1 file)
        if (
                status.nb_workers_commit == 0
                and status.queue_commit.qsize() > 0
                and status.last_commit_attempt is not None
                and time.time() - status.last_commit_attempt > 5 * 60
        ):
            status.nb_workers_commit += 1
            logger.debug("job: commit (more than 5 minutes since last commit attempt)")
            return (WorkerJob.COMMIT, _get_items_to_commit(status.queue_commit))

        # Commit if at least 100 files are ready to commit
        elif status.nb_workers_commit == 0 and status.queue_commit.qsize() >= 150:
            status.nb_workers_commit += 1
            logger.debug("job: commit (>100 files ready)")
            return (WorkerJob.COMMIT, _get_items_to_commit(status.queue_commit))

        # Get upload mode if at least 10 files
        elif status.queue_get_upload_mode.qsize() >= 10:
            status.nb_workers_get_upload_mode += 1
            logger.debug("job: get upload mode (>10 files ready)")
            return (WorkerJob.GET_UPLOAD_MODE, _get_n(status.queue_get_upload_mode, 50))

        # Do uploading lfs multipart if at least 1 slice of lfs file
        elif status.queue_uploading_lfs.qsize() > 0:
            status.nb_workers_uploading_lfs += 1
            logger.debug("job: uploading lfs part")
            return (WorkerJob.UPLOADING_LFS, _get_one(status.queue_uploading_lfs))

        # Preupload LFS file if at least 1 file and no worker is preuploading LFS
        elif status.queue_preupload_lfs.qsize() > 0 and status.nb_workers_preupload_lfs == 0:
            status.nb_workers_preupload_lfs += 1
            logger.debug("job: preupload LFS (no other worker preuploading LFS)")
            return (WorkerJob.PREUPLOAD_LFS, _get_one(status.queue_preupload_lfs))

        # Compute sha256 if at least 1 file and no worker is computing sha256
        elif status.queue_sha256.qsize() > 0 and status.nb_workers_sha256 == 0:
            status.nb_workers_sha256 += 1
            logger.debug("job: sha256 (no other worker computing sha256)")
            return (WorkerJob.SHA256, _get_one(status.queue_sha256))

        # Get upload mode if at least 1 file and no worker is getting upload mode
        elif status.queue_get_upload_mode.qsize() > 0 and status.nb_workers_get_upload_mode == 0:
            status.nb_workers_get_upload_mode += 1
            logger.debug("job: get upload mode (no other worker getting upload mode)")
            return (WorkerJob.GET_UPLOAD_MODE, _get_n(status.queue_get_upload_mode, 50))

        # Preupload LFS file if at least 1 file
        elif status.queue_preupload_lfs.qsize() > 0 and (
                status.nb_workers_preupload_lfs == 0
        ):
            status.nb_workers_preupload_lfs += 1
            logger.debug("job: preupload LFS")
            return (WorkerJob.PREUPLOAD_LFS, _get_one(status.queue_preupload_lfs))

        # Compute sha256 if at least 1 file
        elif status.queue_sha256.qsize() > 0:
            status.nb_workers_sha256 += 1
            logger.debug("job: sha256")
            return (WorkerJob.SHA256, _get_one(status.queue_sha256))

        # Get upload mode if at least 1 file
        elif status.queue_get_upload_mode.qsize() > 0:
            status.nb_workers_get_upload_mode += 1
            logger.debug("job: get upload mode")
            return (WorkerJob.GET_UPLOAD_MODE, _get_n(status.queue_get_upload_mode, 50))

        # Commit if at least 1 file and 1 min since last commit attempt
        elif (
                status.nb_workers_commit == 0
                and status.queue_commit.qsize() > 0
                and status.last_commit_attempt is not None
                and time.time() - status.last_commit_attempt > 1 * 60
        ):
            status.nb_workers_commit += 1
            logger.debug("job: commit (1 min since last commit attempt)")
            return (WorkerJob.COMMIT, _get_items_to_commit(status.queue_commit))

        # Commit if at least 1 file all other queues are empty and all workers are waiting
        # e.g. when it's the last commit
        elif (
                status.nb_workers_commit == 0
                and status.queue_commit.qsize() > 0
                and status.queue_sha256.qsize() == 0
                and status.queue_get_upload_mode.qsize() == 0
                and status.queue_preupload_lfs.qsize() == 0
                and status.nb_workers_sha256 == 0
                and status.nb_workers_get_upload_mode == 0
                and status.nb_workers_preupload_lfs == 0
        ):
            status.nb_workers_commit += 1
            logger.debug("job: commit")
            return (WorkerJob.COMMIT, _get_items_to_commit(status.queue_commit))

        # If all queues are empty, exit
        elif all(metadata.is_committed or metadata.should_ignore for _, metadata in status.items):
            logger.info("all files have been processed! Exiting worker.")
            return None

        # If no task is available, wait
        else:
            status.nb_workers_waiting += 1
            logger.debug(f"no task available, waiting... ({WAITING_TIME_IF_NO_TASKS}s)")
            return (WorkerJob.WAIT, [])


def _get_items_to_commit(queue: "queue.Queue[JOB_ITEM_T]") -> List[JOB_ITEM_T]:
    """Special case for commit job: the number of items to commit depends on the type of files."""
    # Can take at most 50 regular files and/or 100 LFS files in a single commit
    items: List[JOB_ITEM_T] = []
    nb_lfs, nb_regular = 0, 0
    while True:
        # If empty queue => commit everything
        if queue.qsize() == 0:
            return items

        # If we have enough items => commit them
        if nb_lfs >= MAX_NB_LFS_FILES_PER_COMMIT or nb_regular >= MAX_NB_REGULAR_FILES_PER_COMMIT:
            return items

        # Else, get a new item and increase counter
        item = queue.get()
        items.append(item)
        _, metadata = item
        if metadata.upload_mode == "lfs":
            nb_lfs += 1
        else:
            nb_regular += 1


def _get_one(queue: "queue.Queue[JOB_ITEM_T]") -> List[JOB_ITEM_T]:
    return [queue.get()]


def _get_n(queue: "queue.Queue[JOB_ITEM_T]", n: int) -> List[JOB_ITEM_T]:
    return [queue.get() for _ in range(min(queue.qsize(), n))]
