# Copyright (c) Alibaba, Inc. and its affiliates.

import os
import tempfile
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Dict, List, Optional, Union
from pycsghub.utils import get_file_download_url, model_id_to_group_owner_name
from pycsghub.cache import ModelFileSystemCache
from pycsghub.utils import (get_cache_dir,
                   pack_model_file_info,
                            get_endpoint)
from huggingface_hub.utils import filter_repo_objects
from pycsghub.file_download import http_get
from pycsghub.constants import DEFAULT_REVISION
from pycsghub import utils


def snapshot_download(
    repo_id: str,
    *,
    revision: Optional[str] = DEFAULT_REVISION,
    cache_dir: Union[str, Path, None] = None,
    user_agent: Optional[Union[Dict, str]] = None,
    local_files_only: Optional[bool] = False,
    cookies: Optional[CookieJar] = None,
    ignore_file_pattern: List = None,
    allow_patterns: Optional[Union[List[str], str]] = None,
    ignore_patterns: Optional[Union[List[str], str]] = None,
    headers: Optional[Dict[str, str]] = None,
    endpoint: Optional[str] = None,
    token: Optional[str] = None
) -> str:
    if cache_dir is None:
        cache_dir = get_cache_dir()
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)
    temporary_cache_dir = os.path.join(cache_dir, 'temp')
    os.makedirs(temporary_cache_dir, exist_ok=True)

    group_or_owner, name = model_id_to_group_owner_name(repo_id)
    name = name.replace('.', '___')

    cache = ModelFileSystemCache(cache_dir, group_or_owner, name)

    if local_files_only:
        if len(cache.cached_files) == 0:
            raise ValueError(
                'Cannot find the requested files in the cached path and outgoing'
                ' traffic has been disabled. To enable model look-ups and downloads'
                " online, set 'local_files_only' to False.")
        return cache.get_root_location()
    else:
        # make headers
        # todo need to add cookies？
        repo_info = utils.get_repo_info(repo_id,
                                        revision=revision,
                                        token=token,
                                        endpoint=endpoint if endpoint else get_endpoint())

        assert repo_info.sha is not None, "Repo info returned from server must have a revision sha."
        assert repo_info.siblings is not None, "Repo info returned from server must have a siblings list."
        model_files = list(
            filter_repo_objects(
                items=[f.rfilename for f in repo_info.siblings],
                allow_patterns=allow_patterns,
                ignore_patterns=ignore_patterns,
            )
        )

        with tempfile.TemporaryDirectory(
                dir=temporary_cache_dir) as temp_cache_dir:
            for model_file in model_files:
                model_file_info = pack_model_file_info(model_file, revision)
                if cache.exists(model_file_info):
                    file_name = os.path.basename(model_file_info['Path'])
                    print(
                        f'File {file_name} already in cache, skip downloading!'
                    )
                    continue

                # get download url
                url = get_file_download_url(
                    model_id=repo_id,
                    file_path=model_file,
                    revision=revision)
                # todo support parallel download api
                http_get(
                    url=url,
                    local_dir=temp_cache_dir,
                    file_name=model_file,
                    headers=headers,
                    cookies=cookies,
                    token=token)

                # todo using hash to check file integrity
                temp_file = os.path.join(temp_cache_dir, model_file)
                cache.put_file(model_file_info, temp_file)

        cache.save_model_version(revision_info={'Revision': revision})
        return os.path.join(cache.get_root_location())
