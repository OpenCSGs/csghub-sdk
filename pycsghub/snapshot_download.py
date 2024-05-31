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


#logger = get_logger() # todo logger


def snapshot_download(repo_id: str,
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
                      endpoint: Optional[str] = None, #todo 这里后续放成环境变量
                      token: Optional[str] = None #todo 这里后续放成环境变量
                      ) -> str:
    if cache_dir is None:
        cache_dir = get_cache_dir() #todo cache dir
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
        # logger.warning('We can not confirm the cached file is for revision: %s'
        #                % revision)
        return cache.get_root_location(
        )  # we can not confirm the cached file is for snapshot 'revision'
    else:
        # make headers
        # headers = {
        #     'user-agent':
        #         ModelScopeConfig.get_user_agent(user_agent=user_agent, )
        # } todo headers 暂时不加 user-agent
        # if cookies is None: # todo cookies询问是否需要加？
        #     cookies = ModelScopeConfig.get_cookies()
        repo_info = utils.get_repo_info(repo_id,
                                        revision=revision,
                                        token=token,
                                        endpoint=endpoint if endpoint else get_endpoint())

        # todo 这边是否需要支持？
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
                # check model_file is exist in cache, if existed, skip download, otherwise download todo 待解决
                if cache.exists(model_file_info):
                    file_name = os.path.basename(model_file_info['Path'])
                    # logger.debug(
                    #     f'File {file_name} already in cache, skip downloading!'
                    # )
                    continue

                # get download url
                url = get_file_download_url(
                    model_id=repo_id,
                    file_path=model_file,
                    revision=revision)
                # todo 支持并行下载或者下载api
                http_get(
                    url=url,
                    local_dir=temp_cache_dir,
                    file_name=model_file,
                    headers=headers,
                    cookies=cookies,
                    token=token)

                # check file integrity todo 待完善
                temp_file = os.path.join(temp_cache_dir, model_file)
                # if FILE_HASH in model_file:
                #     file_integrity_validation(temp_file, model_file[FILE_HASH]) todo 待完善
                # put file into to cache
                cache.put_file(model_file_info, temp_file)

        cache.save_model_version(revision_info={'Revision': revision}) # todo 待完善
        return os.path.join(cache.get_root_location())
