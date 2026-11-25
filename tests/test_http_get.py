import os
from unittest import mock

import pytest
import requests

from pycsghub import file_download


class FakeResponse:
    def __init__(self, status=200, chunks=(), headers=None, fail_after=None):
        self.status_code = status
        self.headers = headers or {}
        self._chunks = chunks
        self._fail_after = fail_after

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code), response=self)

    def iter_content(self, chunk_size=None):
        for i, c in enumerate(self._chunks):
            if self._fail_after is not None and i >= self._fail_after:
                raise requests.ConnectionError("boom")
            yield c


@pytest.fixture(autouse=True)
def no_sleep():
    with mock.patch("urllib3.util.retry.Retry.sleep"):
        yield


def test_client_error_is_not_retried(tmp_path):
    with mock.patch.object(file_download.requests, "get", return_value=FakeResponse(401)) as get:
        with pytest.raises(requests.HTTPError):
            file_download.http_get(url="http://x/f", local_dir=str(tmp_path), file_name="f", quiet=True)
    assert get.call_count == 1
    assert os.listdir(tmp_path) == []


def test_server_error_is_retried(tmp_path):
    responses = [FakeResponse(503), FakeResponse(200, [b"abc"], {"Content-Length": "3"})]
    with mock.patch.object(file_download.requests, "get", side_effect=responses) as get:
        file_download.http_get(url="http://x/f", local_dir=str(tmp_path), file_name="f", quiet=True)
    assert get.call_count == 2
    assert (tmp_path / "f").read_bytes() == b"abc"


def test_restart_without_range_support_has_no_hole(tmp_path):
    # first attempt writes 4 bytes then drops; server has no Accept-Ranges,
    # so the second attempt resends the whole body from offset 0
    responses = [
        FakeResponse(200, [b"ABCD", b"EF"], {}, fail_after=1),
        FakeResponse(200, [b"ABCDEF"], {"Content-Length": "6"}),
    ]
    with mock.patch.object(file_download.requests, "get", side_effect=responses):
        file_download.http_get(url="http://x/f", local_dir=str(tmp_path), file_name="f", quiet=True)
    assert (tmp_path / "f").read_bytes() == b"ABCDEF"


def test_client_error_survives_temp_file_removal_failure(tmp_path):
    response = FakeResponse(401)
    with mock.patch.object(file_download.requests, "get", return_value=response) as get:
        with mock.patch.object(file_download.os, "remove", side_effect=PermissionError) as remove:
            with pytest.raises(requests.HTTPError) as error:
                file_download.http_get(url="http://x/f", local_dir=str(tmp_path), file_name="f", quiet=True)
    assert error.value.response is response
    remove.assert_called_once()
    get.assert_called_once()
