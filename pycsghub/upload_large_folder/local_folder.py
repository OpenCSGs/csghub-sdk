import logging
import os
import time
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict
from .fixes import WeakFileLock

logger = logging.getLogger(__name__)

key_timestamp = "timestamp"
key_size = "size"
key_should_ignore = "should_ignore"
key_sha256 = "sha256"
key_sha1 = "sha1"
key_upload_mode = "upload_mode"
key_is_uploaded = "is_uploaded"
key_is_committed = "is_committed"
key_lfs_upload_id = "lfs_upload_id"
key_lfs_part_count = "lfs_part_count"
key_lfs_uploaded_ids = "lfs_uploaded_ids"
key_remote_oid = "remote_oid"

cache_path = ".cache"
cache_csghub = "csghub"

@dataclass(frozen=True)
class LocalUploadFilePaths:
    path_in_repo: str
    file_path: Path
    lock_path: Path
    metadata_path: Path
    
@dataclass
class LocalUploadFileMetadata:
    """Metadata for a file that is being uploaded to the hub."""
    size: int

    timestamp: Optional[float] = None
    should_ignore: Optional[bool] = None
    sha256: Optional[str] = None
    sha1: Optional[str] = None
    upload_mode: Optional[str] = None  # regular | lfs
    is_uploaded: bool = False
    is_committed: bool = False
    
    remote_oid: Optional[str] = None # remote oid
    lfs_upload_id: Optional[str] = None # upload id, only used for multipart uploads
    lfs_uploaded_ids: Optional[str] = None # uploaded ids

    # only for runtime
    lfs_upload_part_count: Optional[int] = None # total number of parts, only used for multipart uploads
    lfs_upload_part_index: Optional[int] = None # index of part, only used for multipart uploads
    lfs_upload_part_url: Optional[str] = None # upload url for part
    lfs_upload_chunk_size: Optional[int] = None
    lfs_upload_complete_url: Optional[str] = None # for merge multi-part
    lfs_upload_verify: Optional[Dict] = None # for verify
    content_base64: str = ""
    
    def save(self, paths: LocalUploadFilePaths) -> None:
        """Save the metadata to disk."""
        with WeakFileLock(paths.lock_path):
            new_timestamp = time.time()
            metadata = {
                key_timestamp: time.time(),
                key_size: str(self.size),
                key_should_ignore: "" if self.should_ignore is None else str(self.should_ignore),
                key_sha256: "" if self.sha256 is None else self.sha256,
                key_sha1: "" if self.sha1 is None else self.sha1,
                key_upload_mode: "" if self.upload_mode is None else self.upload_mode,
                key_is_uploaded: str(self.is_uploaded),
                key_is_committed: str(self.is_committed),
                key_remote_oid: "" if self.remote_oid is None else self.remote_oid,
                key_lfs_upload_id: "" if self.lfs_upload_id is None else self.lfs_upload_id,
                key_lfs_part_count: "" if self.lfs_upload_part_count is None else str(self.lfs_upload_part_count),
                key_lfs_uploaded_ids: "" if self.lfs_uploaded_ids is None else self.lfs_uploaded_ids,
            }
            save_properties(paths.metadata_path, metadata)
            self.timestamp = new_timestamp

def read_upload_metadata(local_dir: Path, filename: str) -> LocalUploadFileMetadata:
    paths = get_local_upload_paths(local_dir, filename)
    with WeakFileLock(paths.lock_path):
        if paths.metadata_path.exists():
            try:
                props = read_properties(paths.metadata_path)
                
                timestamp = float(props.get(key_timestamp))
                
                size = int(props.get(key_size))
                
                _should_ignore = props.get(key_should_ignore)
                should_ignore = None if _should_ignore == "" else _should_ignore.lower() == "true"
                
                sha256 = props.get(key_sha256)
                sha1 = props.get(key_sha1)
                
                _upload_mode = props.get(key_upload_mode)
                upload_mode = None if _upload_mode == "" else _upload_mode
                
                is_uploaded = props.get(key_is_uploaded).lower() == "true"
                is_committed = props.get(key_is_committed).lower() == "true"

                _lfs_upload_id = props.get(key_lfs_upload_id)
                lfs_upload_id = None if _lfs_upload_id == "" else _lfs_upload_id
                _lfs_uploaded_ids = props.get(key_lfs_uploaded_ids)
                lfs_uploaded_ids = None if _lfs_uploaded_ids == "" else _lfs_uploaded_ids
                
                metadata = LocalUploadFileMetadata(
                    timestamp=timestamp,
                    size=size,
                    should_ignore=should_ignore,
                    sha256=sha256,
                    sha1=sha1,
                    upload_mode=upload_mode,
                    is_uploaded=is_uploaded,
                    is_committed=is_committed,
                    lfs_upload_id=lfs_upload_id,
                    lfs_uploaded_ids=lfs_uploaded_ids,
                )
            except Exception as e:
                # remove the metadata file if it is corrupted / not the right format
                logger.warning(f"invalid metadata file {paths.metadata_path}: {e}. Removing it from disk and continue.")
                try:
                    paths.metadata_path.unlink()
                except Exception as e:
                    logger.warning(f"could not remove corrupted metadata file {paths.metadata_path}: {e}")

            if (
                metadata.timestamp is not None
                and metadata.is_uploaded  # file was uploaded
                and not metadata.is_committed  # but not committed
                and time.time() - metadata.timestamp > 20 * 3600  # and it's been more than 20 hours
            ):
                metadata.is_uploaded = False

            # check if the file exists and hasn't been modified since the metadata was saved
            try:
                if metadata.timestamp is not None and paths.file_path.stat().st_mtime <= metadata.timestamp:
                    return metadata
                logger.info(f"ignored metadata for '{filename}' (outdated) and will re-compute hash.")
            except FileNotFoundError:
                # file does not exist => metadata is outdated
                pass

    # empty metadata => we don't know anything expect its size
    return LocalUploadFileMetadata(size=paths.file_path.stat().st_size)

def read_properties(file_path):
    config = ConfigParser()
    with open(file_path, 'r', encoding='utf-8') as f:
        config.read_string(f.read())
    return dict(config['DEFAULT'])

def save_properties(file_path: str, data: dict) -> None:
    config = ConfigParser()
    config['DEFAULT'] = data
    with open(file_path, 'w', encoding='utf-8') as f:
        config.write(f, space_around_delimiters=False)

def get_local_upload_paths(local_dir: Path, filename: str) -> LocalUploadFilePaths:
    sanitized_filename = os.path.join(*filename.split("/"))
    if os.name == "nt":
        if sanitized_filename.startswith("..\\") or "\\..\\" in sanitized_filename:
            raise ValueError(
                f"Invalid filename: cannot handle filename '{sanitized_filename}' on Windows. Please ask the repository"
                " owner to rename this file."
            )
    file_path = local_dir / sanitized_filename
    metadata_path = csghub_dir(local_dir) / "upload" / f"{sanitized_filename}.metadata"
    lock_path = metadata_path.with_suffix(".lock")

    # Some Windows versions do not allow for paths longer than 255 characters.
    # In this case, we must specify it as an extended path by using the "\\?\" prefix
    if os.name == "nt":
        if not str(local_dir).startswith("\\\\?\\") and len(os.path.abspath(lock_path)) > 255:
            file_path = Path("\\\\?\\" + os.path.abspath(file_path))
            lock_path = Path("\\\\?\\" + os.path.abspath(lock_path))
            metadata_path = Path("\\\\?\\" + os.path.abspath(metadata_path))

    file_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    return LocalUploadFilePaths(
        path_in_repo=filename, file_path=file_path, lock_path=lock_path, metadata_path=metadata_path
    )


def csghub_dir(local_dir: Path) -> Path:
    path = local_dir / cache_path / cache_csghub
    path.mkdir(exist_ok=True, parents=True)

    gitignore = path / ".gitignore"
    gitignore_lock = path / ".gitignore.lock"
    if not gitignore.exists():
        try:
            with WeakFileLock(gitignore_lock):
                gitignore.write_text("*")
            gitignore_lock.unlink()
        except OSError:
            pass
    return path
