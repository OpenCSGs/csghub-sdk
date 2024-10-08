# Copyright (c) Alibaba, Inc. and its affiliates.

import os
import tempfile
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Dict, List, Optional, Union
from pycsghub.utils import (get_file_download_url,
                            model_id_to_group_owner_name)
from pycsghub.cache import ModelFileSystemCache
from pycsghub.utils import (get_cache_dir,
                            pack_repo_file_info,
                            get_endpoint)
from huggingface_hub.utils import filter_repo_objects
from pycsghub.file_download import http_get
from pycsghub.constants import DEFAULT_REVISION, REPO_TYPES, MIRROR
from pycsghub import utils
from pycsghub.constants import REPO_TYPE_MODEL


def snapshot_download(
        repo_id: str,
        *,
        repo_type: Optional[str] = None,
        revision: Optional[str] = DEFAULT_REVISION,
        cache_dir: Union[str, Path, None] = None,
        local_files_only: Optional[bool] = False,
        cookies: Optional[CookieJar] = None,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        headers: Optional[Dict[str, str]] = None,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        mirror: Optional[str] = MIRROR.AUTO,
) -> str:
    if repo_type is None:
        repo_type = REPO_TYPE_MODEL
    if repo_type not in REPO_TYPES:
        raise ValueError(f"Invalid repo type: {repo_type}. Accepted repo types are: {str(REPO_TYPES)}")
    if cache_dir is None:
        cache_dir = get_cache_dir(repo_type=repo_type)
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)
    temporary_cache_dir = os.path.join(cache_dir, 'temp')
    os.makedirs(temporary_cache_dir, exist_ok=True)

    group_or_owner, name = model_id_to_group_owner_name(repo_id)
    # name = name.replace('.', '___')

    cache = ModelFileSystemCache(cache_dir, group_or_owner, name)

    if local_files_only:
        if len(cache.cached_files) == 0:
            raise ValueError(
                'Cannot find the requested files in the cached path and outgoing'
                ' traffic has been disabled. To enable model look-ups and downloads'
                " online, set 'local_files_only' to False.")
        return cache.get_root_location()
    else:
        download_endpoint = get_endpoint(endpoint=endpoint)
        # make headers
        # todo need to add cookies？
        repo_info = utils.get_repo_info(repo_id,
                                        repo_type=repo_type,
                                        revision=revision,
                                        token=token,
                                        endpoint=download_endpoint,
                                        mirror=mirror)

        assert repo_info.sha is not None, "Repo info returned from server must have a revision sha."
        assert repo_info.siblings is not None, "Repo info returned from server must have a siblings list."
        repo_files = list(
            filter_repo_objects(
                items=[f.rfilename for f in repo_info.siblings],
                allow_patterns=allow_patterns,
                ignore_patterns=ignore_patterns,
            )
        )

        with tempfile.TemporaryDirectory(dir=temporary_cache_dir) as temp_cache_dir:
            for repo_file in repo_files:
                repo_file_info = pack_repo_file_info(repo_file, revision)
                if cache.exists(repo_file_info):
                    file_name = os.path.basename(repo_file_info['Path'])
                    print(f"File {file_name} already in cache '{cache.get_root_location()}', skip downloading!")
                    continue

                # get download url
                url = get_file_download_url(
                    model_id=repo_id,
                    file_path=repo_file,
                    repo_type=repo_type,
                    revision=revision,
                    endpoint=download_endpoint,
                    mirror=mirror,
                )
                # todo support parallel download api
                http_get(
                    url=url,
                    local_dir=temp_cache_dir,
                    file_name=repo_file,
                    headers=headers,
                    cookies=cookies,
                    token=token)

                # todo using hash to check file integrity
                temp_file = os.path.join(temp_cache_dir, repo_file)
                savedFile = cache.put_file(repo_file_info, temp_file)
                print(f"Saved file to '{savedFile}'")
            
        cache.save_model_version(revision_info={'Revision': revision})
        return os.path.join(cache.get_root_location())
