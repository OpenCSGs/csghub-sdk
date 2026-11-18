import pytest
import requests

from pycsghub.upload_large_folder import slices, workers
from pycsghub.upload_large_folder.consts import LFS_COMPLETE_MAX_FAILURES, REPO_LFS_TYPE
from pycsghub.upload_large_folder.local_folder import (
    LocalUploadFileMetadata,
    get_local_upload_paths,
    read_upload_metadata,
)
from pycsghub.upload_large_folder.status import LargeUploadStatus

REL_PATH = "model.bin"
UPLOADED_IDS = "1:etag-1,2:etag-2"


def _make_item(tmp_path):
    (tmp_path / REL_PATH).write_bytes(b"x" * 64)
    paths = get_local_upload_paths(tmp_path, REL_PATH)
    metadata = LocalUploadFileMetadata(
        size=64,
        sha256="a" * 64,
        upload_mode=REPO_LFS_TYPE,
        remote_oid="a" * 64,
        lfs_upload_id="old-upload-id",
        lfs_uploaded_ids=UPLOADED_IDS,
        lfs_upload_part_count=2,
        lfs_upload_complete_url="https://example.test/complete",
    )
    metadata.save(paths)
    return paths, metadata


def _response(status_code):
    response = requests.Response()
    response.status_code = status_code
    response._content = b'{"message":"missing part"}'
    response.url = "https://example.test/complete"
    return response


def test_repeated_complete_failures_clear_cached_parts(tmp_path):
    item = _make_item(tmp_path)
    paths, _ = item
    status = LargeUploadStatus([item])

    assert status.get_lfs_uploaded_slice_ids(paths.file_path) == UPLOADED_IDS

    for _ in range(LFS_COMPLETE_MAX_FAILURES - 1):
        assert status.record_lfs_complete_failure(item) is False

    assert status.record_lfs_complete_failure(item) is True
    assert status.get_lfs_uploaded_slice_ids(paths.file_path) is None

    cached = read_upload_metadata(tmp_path, REL_PATH)
    assert cached.lfs_uploaded_ids is None
    assert cached.lfs_upload_id is None
    assert cached.lfs_upload_part_count is None
    assert cached.is_uploaded is False


def test_4xx_complete_failure_clears_cache_immediately(tmp_path):
    item = _make_item(tmp_path)
    paths, _ = item
    status = LargeUploadStatus([item])

    assert status.record_lfs_complete_failure(item, fatal=True) is True
    assert status.get_lfs_uploaded_slice_ids(paths.file_path) is None

    cached = read_upload_metadata(tmp_path, REL_PATH)
    assert cached.lfs_uploaded_ids is None
    assert cached.lfs_upload_id is None


def test_successful_complete_resets_failure_counter(tmp_path):
    item = _make_item(tmp_path)
    paths, _ = item
    status = LargeUploadStatus([item])

    for _ in range(3):
        assert status.record_lfs_complete_failure(item) is False

    status.reset_lfs_complete_failures(paths.file_path)

    for _ in range(3):
        assert status.record_lfs_complete_failure(item) is False


@pytest.mark.parametrize("status_code", [302, 400, 404, 500])
def test_slices_upload_complete_raises_for_error_status(monkeypatch, tmp_path, status_code):
    item = _make_item(tmp_path)

    response = _response(status_code)
    monkeypatch.setattr(slices.requests, "post", lambda *args, **kwargs: response)

    with pytest.raises(requests.HTTPError):
        slices.slices_upload_complete(item=item, uploaded_ids_map={"1": "etag-1", "2": "etag-2"})


def test_preupload_failure_records_and_clears_cache(monkeypatch, tmp_path):
    item = _make_item(tmp_path)
    status = LargeUploadStatus([item])
    status.nb_workers_preupload_lfs = 1

    def fake_complete(item, uploaded_ids_map):
        raise requests.HTTPError("complete rejected", response=_response(404))

    monkeypatch.setattr(workers, "slices_upload_complete", fake_complete)

    workers._execute_job_pre_upload_lfs(
        items=[item],
        status=status,
        api=None,
        endpoint=None,
        token=None,
        repo_id="owner/repo",
        repo_type="model",
        revision="main",
    )

    cached = read_upload_metadata(tmp_path, REL_PATH)
    assert cached.lfs_uploaded_ids is None
    assert cached.lfs_upload_id is None
