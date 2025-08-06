import io
import logging
from typing import Dict

import requests
from tqdm import tqdm

from .status import JOB_ITEM_T

logger = logging.getLogger(__name__)


class UploadTracker(io.BytesIO):
    def __init__(self, data, progress_bar):
        super().__init__(data)
        self._progress_bar = progress_bar

    def read(self, size=-1):
        chunk = super().read(size)
        self._progress_bar.update(len(chunk))
        return chunk


def slice_upload(item: JOB_ITEM_T):
    paths, metadata = item
    upload_desc = f"uploading {paths.file_path}({metadata.lfs_upload_part_index}/{metadata.lfs_upload_part_count})"

    read_chunk_size = metadata.lfs_upload_chunk_size
    if metadata.lfs_upload_part_index == metadata.lfs_upload_part_count:
        read_chunk_size = metadata.size - (metadata.lfs_upload_part_count - 1) * metadata.lfs_upload_chunk_size

    chunk_data = None
    with paths.file_path.open('rb') as f:
        f.seek((metadata.lfs_upload_part_index - 1) * metadata.lfs_upload_chunk_size)
        chunk_data = f.read(read_chunk_size)

    total = len(chunk_data)
    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Length": str(total)
    }
    with tqdm(initial=0, total=total, desc=upload_desc, unit="B", unit_scale=True, dynamic_ncols=True) as pbar:
        upload_data = UploadTracker(chunk_data, pbar)
        response = requests.put(
            url=metadata.lfs_upload_part_url,
            headers=headers,
            data=upload_data,
        )
        if response.status_code != 200:
            logger.error(
                f"LFS slice {paths.file_path}({metadata.lfs_upload_part_index}/{metadata.lfs_upload_part_count}) upload on {metadata.lfs_upload_part_url} response: {response.text}")
        response.raise_for_status()
        return response.headers


def slices_upload_complete(item: JOB_ITEM_T, uploaded_ids_map: Dict):
    paths, metadata = item
    payload = {
        "oid": metadata.sha256,
        "uploadId": metadata.lfs_upload_id,
        "parts": [
            {"partNumber": i + 1, "etag": f"{uploaded_ids_map.get(str(i + 1))}"}
            for i in range(metadata.lfs_upload_part_count)
        ]
    }
    response = requests.post(metadata.lfs_upload_complete_url, json=payload)
    if response.status_code != 200 and (response.status_code < 400 or response.status_code >= 500):
        logger.error(
            f"LFS {paths.file_path} merge all uploaded slices complete on {metadata.lfs_upload_complete_url} response: {response.text}")
    if response.status_code < 400 or response.status_code >= 500:
        response.raise_for_status()
    return response.text


def slices_upload_verify(item: JOB_ITEM_T):
    paths, metadata = item
    payload = {
        "oid": metadata.sha256,
        "size": metadata.size,
    }
    verify_url = metadata.lfs_upload_verify.get("href")
    verify_header = metadata.lfs_upload_verify.get("header")
    response = requests.post(verify_url, headers=verify_header, json=payload)
    if response.status_code != 200:
        logger.error(
            f"LFS {paths.file_path} slices uploaded verify on {verify_url} response: {response.text}, delete file {paths.metadata_path} and retry")
    response.raise_for_status()
    return response.text
