import os

import pytest

from pycsghub.cache import ModelFileSystemCache
from pycsghub.file_download import file_download
from pycsghub.utils import pack_repo_file_info

REPO_ID = "owner/repo"
FILE_NAME = "README.md"


def _seed_cache(cache_dir, tmp_path):
    """Create a cache containing README.md for owner/repo."""
    cache = ModelFileSystemCache(str(cache_dir), "owner", "repo")
    source = tmp_path / "src" / FILE_NAME
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("hello")
    cache.put_file(pack_repo_file_info(FILE_NAME, "main"), str(source))
    return cache


def test_local_files_only_returns_file_path(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    _seed_cache(cache_dir, tmp_path)

    result = file_download(
        repo_id=REPO_ID,
        file_name=FILE_NAME,
        repo_type="model",
        cache_dir=str(cache_dir),
        local_files_only=True,
    )

    expected = os.path.join(str(cache_dir), "owner", "repo", FILE_NAME)
    assert result == expected
    assert os.path.isfile(result)


def test_local_files_only_raises_when_file_not_cached(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    _seed_cache(cache_dir, tmp_path)

    with pytest.raises(ValueError, match="Cannot find file 'other.md'"):
        file_download(
            repo_id=REPO_ID,
            file_name="other.md",
            repo_type="model",
            cache_dir=str(cache_dir),
            local_files_only=True,
        )


def test_local_files_only_raises_when_cached_file_deleted(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    _seed_cache(cache_dir, tmp_path)

    # Remove the cached file from disk; the index still references it.
    cached_file = cache_dir / "owner" / "repo" / FILE_NAME
    os.remove(cached_file)

    with pytest.raises(ValueError, match="Cannot find file 'README.md'"):
        file_download(
            repo_id=REPO_ID,
            file_name=FILE_NAME,
            repo_type="model",
            cache_dir=str(cache_dir),
            local_files_only=True,
        )


def test_local_files_only_raises_on_empty_cache(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    with pytest.raises(ValueError, match="local cache"):
        file_download(
            repo_id=REPO_ID,
            file_name=FILE_NAME,
            repo_type="model",
            cache_dir=str(cache_dir),
            local_files_only=True,
        )


def test_repo_type_defaults_to_model_when_omitted(tmp_path, monkeypatch):
    """file_download() without repo_type must not fail with 'invalid repo type'."""
    from pycsghub import file_download as fd_module

    seen = {}

    class _Stop(Exception):
        pass

    def fake_get_repo_info(**kwargs):
        seen.update(kwargs)
        raise _Stop()

    monkeypatch.setattr(fd_module.utils, "get_repo_info", fake_get_repo_info)

    with pytest.raises(_Stop):
        file_download(
            repo_id=REPO_ID,
            file_name=FILE_NAME,
            cache_dir=str(tmp_path / "cache"),
            endpoint="http://localhost",
        )
    assert seen["repo_type"] == "model"
