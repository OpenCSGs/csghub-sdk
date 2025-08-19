import base64
import enum
import logging
import queue
from datetime import datetime
from io import BytesIO
from threading import Lock
from typing import List, Optional, Tuple

from tqdm import tqdm

from .consts import META_FILE_IDENTIFIER, META_FILE_OID_PREFIX
from .consts import REPO_LFS_TYPE, REPO_REGULAR_TYPE
from .local_folder import LocalUploadFileMetadata, LocalUploadFilePaths

logger = logging.getLogger(__name__)

JOB_ITEM_T = Tuple[LocalUploadFilePaths, LocalUploadFileMetadata]


class WorkerJob(enum.Enum):
    SHA256 = enum.auto()
    GET_UPLOAD_MODE = enum.auto()
    PREUPLOAD_LFS = enum.auto()
    UPLOADING_LFS = enum.auto()
    COMMIT = enum.auto()
    WAIT = enum.auto()  # if no tasks are available but we don't want to exit


class ProgressReader:
    def __init__(self, fileobj, progress_bar):
        self.fileobj = fileobj
        self.progress_bar = progress_bar

    def read(self, size=-1):
        data = self.fileobj.read(size)
        if data:
            self.progress_bar.update(len(data))
        return data


class LargeUploadStatus:
    """Contains information, queues and tasks for a large upload process."""

    def __init__(self, items: List[JOB_ITEM_T]):
        self.items = items
        self.queue_sha256: "queue.Queue[JOB_ITEM_T]" = queue.Queue()
        self.queue_get_upload_mode: "queue.Queue[JOB_ITEM_T]" = queue.Queue()
        self.queue_preupload_lfs: "queue.Queue[JOB_ITEM_T]" = queue.Queue()
        self.queue_uploading_lfs: "queue.Queue[JOB_ITEM_T]" = queue.Queue()
        self.queue_commit: "queue.Queue[JOB_ITEM_T]" = queue.Queue()
        self.lock = Lock()

        self.nb_workers_sha256: int = 0
        self.nb_workers_get_upload_mode: int = 0
        self.nb_workers_preupload_lfs: int = 0
        self.nb_workers_uploading_lfs: int = 0
        self.nb_workers_commit: int = 0
        self.nb_workers_waiting: int = 0
        self.last_commit_attempt: Optional[float] = None

        self._started_at = datetime.now()
        self._lfs_uploaded_ids = dict()

        # Setup queues
        num_uploaded_and_commited = 0
        for item in self.items:
            paths, metadata = item
            self._lfs_uploaded_ids[paths.file_path] = metadata.lfs_uploaded_ids

            if (metadata.upload_mode is not None and metadata.upload_mode == REPO_LFS_TYPE
                    and metadata.is_uploaded and metadata.is_committed):
                num_uploaded_and_commited += 1
            elif (metadata.upload_mode is not None and metadata.upload_mode == REPO_REGULAR_TYPE
                  and metadata.is_committed):
                num_uploaded_and_commited += 1
            elif (metadata.sha256 is None or metadata.sha256 == ""):
                self.queue_sha256.put(item)
            elif (metadata.upload_mode is None or metadata.upload_mode == ""
                  or metadata.remote_oid is None or metadata.remote_oid == ""):
                self.queue_get_upload_mode.put(item)
            elif (metadata.upload_mode == REPO_LFS_TYPE and not metadata.is_uploaded):
                self.queue_preupload_lfs.put(item)
            elif (not metadata.is_committed):
                self.queue_commit.put(item)
            else:
                num_uploaded_and_commited += 1
                logger.debug(f"skipping file {paths.path_in_repo} because they are already uploaded and committed")

        log_msg = "init upload status"
        if num_uploaded_and_commited > 0:
            log_msg = f"{log_msg}, found {len(items)} files, {num_uploaded_and_commited} of which are already uploaded and committed"
        else:
            log_msg = f"{log_msg}, found {len(items)} files"
        log_msg = f"{log_msg}, queue(sha): {self.queue_sha256.qsize()}"
        log_msg = f"{log_msg}, queue(mode): {self.queue_get_upload_mode.qsize()}"
        log_msg = f"{log_msg}, queue(preupload): {self.queue_preupload_lfs.qsize()}"
        log_msg = f"{log_msg}, queue(commit): {self.queue_commit.qsize()}"
        logger.info(log_msg)

    def current_report(self) -> str:
        """Generate a report of the current status of the large upload."""
        nb_hashed = 0
        size_hashed = 0
        nb_preuploaded = 0
        nb_lfs = 0
        nb_lfs_unsure = 0
        size_preuploaded = 0
        nb_committed = 0
        size_committed = 0
        total_size = 0
        ignored_files = 0
        total_files = 0
        nb_queued_slices = 0

        with self.lock:
            for _, metadata in self.items:
                if metadata.should_ignore:
                    ignored_files += 1
                    continue
                total_size += metadata.size
                total_files += 1
                if metadata.sha256 is not None:
                    nb_hashed += 1
                    size_hashed += metadata.size
                if metadata.upload_mode == REPO_LFS_TYPE:
                    nb_lfs += 1
                if metadata.upload_mode is None:
                    nb_lfs_unsure += 1
                if metadata.is_uploaded and metadata.upload_mode == REPO_LFS_TYPE:
                    nb_preuploaded += 1
                    size_preuploaded += metadata.size
                if metadata.is_committed:
                    nb_committed += 1
                    size_committed += metadata.size
            total_size_str = _format_size(total_size)
            nb_queued_slices = self.queue_uploading_lfs.qsize()

            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            elapsed = now - self._started_at
            elapsed_str = str(elapsed).split(".")[0]  # remove milliseconds

            message = "\n" + "-" * 10
            message += f" {now_str} ({elapsed_str}) "
            message += "-" * 10 + "\n"

            message += "Files:   "
            message += f"hashed {nb_hashed}/{total_files} ({_format_size(size_hashed)}/{total_size_str}) | "
            message += f"pre-uploaded: {nb_preuploaded}/{nb_lfs} ({_format_size(size_preuploaded)}/{total_size_str})"
            if nb_lfs_unsure > 0:
                message += f" (+{nb_lfs_unsure} unsure)"
            message += f" | queued-slices: {nb_queued_slices}"
            message += f" | committed: {nb_committed}/{total_files} ({_format_size(size_committed)}/{total_size_str})"
            message += f" | ignored: {ignored_files}\n"

            message += "Workers: "
            message += f"hashing: {self.nb_workers_sha256} | "
            message += f"get upload mode: {self.nb_workers_get_upload_mode} | "
            message += f"pre-uploading: {self.nb_workers_preupload_lfs} | "
            message += f"slices-uploading: {self.nb_workers_uploading_lfs} | "
            message += f"committing: {self.nb_workers_commit} | "
            message += f"waiting: {self.nb_workers_waiting}\n"
            message += "-" * 51

            return message

    def is_done(self) -> bool:
        with self.lock:
            return all(metadata.is_committed or metadata.should_ignore for _, metadata in self.items)

    def get_lfs_uploaded_slice_ids(self, file_path: str) -> str:
        with self.lock:
            return self._lfs_uploaded_ids.get(file_path)

    def append_lfs_uploaded_slice_id(self, file_path: str, id: int, etag: str):
        with self.lock:
            old_ids = self._lfs_uploaded_ids.get(file_path)
            id_map = self.convert_uploaded_ids_to_map(old_ids)
            new_ids = ""
            if len(id_map) == 0:
                new_ids = f"{id}:{etag}"
            else:
                if id_map.get(str(id)) is None:
                    new_ids = f"{old_ids},{id}:{etag}"
                else:
                    new_ids = old_ids
            self._lfs_uploaded_ids[file_path] = new_ids

    def convert_uploaded_ids_to_map(self, ids: str):
        id_map = {}
        if ids is None or ids == "":
            return id_map
        for item in ids.split(','):
            idx, etag = item.split(':', 2)
            id_map[idx] = etag
        return id_map

    def is_lfs_upload_completed(self, item: JOB_ITEM_T) -> bool:
        paths, metadata = item
        with self.lock:
            uploaded_ids = self._lfs_uploaded_ids.get(paths.file_path)
            if (uploaded_ids is not None and
                    metadata.lfs_upload_id is not None and
                    metadata.lfs_upload_part_count is not None and
                    len(uploaded_ids.split(",")) == metadata.lfs_upload_part_count):
                metadata.lfs_uploaded_ids = uploaded_ids
                return True
        return False

    def compute_file_base64(self, item: JOB_ITEM_T):
        _, meta = item
        if meta.upload_mode == REPO_LFS_TYPE:
            self._compute_lfs_file_base64(item=item)
        elif meta.upload_mode == REPO_REGULAR_TYPE:
            self._compute_regular_file_base64(item=item)

    def _compute_lfs_file_base64(self, item: JOB_ITEM_T):
        _, meta = item
        content = f"{META_FILE_IDENTIFIER}\n{META_FILE_OID_PREFIX}{meta.sha256}\nsize {meta.size}\n"
        content_bytes = content.encode('utf-8')
        meta.content_base64 = base64.b64encode(content_bytes).decode('utf-8')

    def _compute_regular_file_base64(self, item: JOB_ITEM_T):
        paths, meta = item
        # with open(paths.file_path, 'rb') as f, BytesIO() as b64_buffer:
        #     base64.encode(f, b64_buffer)
        #     meta.content_base64 = b64_buffer.getvalue().decode("utf-8")

        desc = f"converting {paths.file_path} to base64"
        with tqdm(total=meta.size, desc=desc, unit="B", unit_scale=True, dynamic_ncols=True) as pbar:
            with open(paths.file_path, 'rb') as f, BytesIO() as b64_buffer:
                progress_reader = ProgressReader(f, pbar)
                base64.encode(progress_reader, b64_buffer)
                b64_buffer.seek(0)
                meta.content_base64 = b64_buffer.getvalue().decode("utf-8")


def _format_size(num: int) -> str:
    """Format size in bytes into a human-readable string.

    Taken from https://stackoverflow.com/a/1094933
    """
    num_f = float(num)
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num_f) < 1000.0:
            return f"{num_f:3.1f}{unit}"
        num_f /= 1000.0
    return f"{num_f:.1f}Y"
