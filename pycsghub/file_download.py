import tempfile
from functools import partial
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Optional, Union, List, Dict
import requests
from huggingface_hub.utils import filter_repo_objects
from requests.adapters import Retry
from tqdm import tqdm
from pycsghub import utils
from pycsghub.cache import ModelFileSystemCache
from pycsghub.utils import (build_csg_headers,
                            get_cache_dir,
                            model_id_to_group_owner_name,
                            pack_repo_file_info,
                            get_file_download_url,
                            get_endpoint)
from pycsghub.constants import (API_FILE_DOWNLOAD_RETRY_TIMES,
                                API_FILE_DOWNLOAD_TIMEOUT,
                                API_FILE_DOWNLOAD_CHUNK_SIZE,
                                DEFAULT_REVISION)
from pycsghub.errors import FileDownloadError
import os
from pycsghub.errors import InvalidParameter


def try_to_load_from_cache():
    pass


def cached_download():
    pass


def csg_hub_download():
    pass


def get_csg_hub_url():
    pass


def file_download(
        repo_id: str,
        *,
        file_name: str = None,
        revision: Optional[str] = DEFAULT_REVISION,
        cache_dir: Union[str, Path, None] = None,
        local_files_only: Optional[bool] = False,
        cookies: Optional[CookieJar] = None,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        headers: Optional[Dict[str, str]] = None,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        repo_type: Optional[str] = None
) -> str:
    if cache_dir is None:
        cache_dir = get_cache_dir(repo_type=repo_type)
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)
    temporary_cache_dir = os.path.join(cache_dir, 'temp')
    os.makedirs(temporary_cache_dir, exist_ok=True)

    if file_name is None:
        raise InvalidParameter('file_name cannot be None, if you want '
                               'to load single file from repo {}'.format(repo_id))

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
        download_endpoint = get_endpoint(endpoint=endpoint)
        # make headers
        # todo need to add cookies？
        repo_info = utils.get_repo_info(repo_id=repo_id,
                                        revision=revision,
                                        token=token,
                                        endpoint=download_endpoint,
                                        repo_type=repo_type)

        assert repo_info.sha is not None, "Repo info returned from server must have a revision sha."
        assert repo_info.siblings is not None, "Repo info returned from server must have a siblings list."
        model_files = list(
            filter_repo_objects(
                items=[f.rfilename for f in repo_info.siblings],
                allow_patterns=allow_patterns,
                ignore_patterns=ignore_patterns,
            )
        )
        if file_name not in model_files:
            raise InvalidParameter('file {} not in repo {}'.format(file_name, repo_id))

        with tempfile.TemporaryDirectory(
                dir=temporary_cache_dir) as temp_cache_dir:
            repo_file_info = pack_repo_file_info(file_name, revision)
            if not cache.exists(repo_file_info):
                file_name = os.path.basename(repo_file_info['Path'])
                # get download url
                url = get_file_download_url(
                    model_id=repo_id,
                    file_path=file_name,
                    revision=revision,
                    endpoint=download_endpoint,
                    repo_type=repo_type)
                # todo support parallel download api
                http_get(
                    url=url,
                    local_dir=temp_cache_dir,
                    file_name=file_name,
                    headers=headers,
                    cookies=cookies,
                    token=token)

                # todo using hash to check file integrity
                temp_file = os.path.join(temp_cache_dir, file_name)
                cache.put_file(repo_file_info, temp_file)
            else:
                print(
                    f'File {file_name} already in cache {cache.get_root_location()}, skip downloading!'
                )
        cache.save_model_version(revision_info={'Revision': revision})
        return os.path.join(cache.get_root_location(), file_name)


def http_get(*,
             url: str,
             local_dir: str,
             file_name: str,
             headers: dict = None,
             cookies: CookieJar = None,
             token: str = None) -> None:
    '''
    download core API，using python request to download file to local cache dirs
    :param token: csghub token
    :param url: url to download
    :param local_dir: local dir to download
    :param file_name: file name to download
    :param headers: http headers
    :param cookies: http cookies
    :return: None
    '''
    tempfile_mgr = partial(tempfile.NamedTemporaryFile, mode='wb', dir=local_dir, delete=False)
    get_headers = build_csg_headers(token=token, headers=headers)
    total_content_length = 0
    with tempfile_mgr() as temp_file:
        # retry sleep 0.5s, 1s, 2s, 4s
        retry = Retry(total=API_FILE_DOWNLOAD_RETRY_TIMES, backoff_factor=1, allowed_methods=['GET'])
        while True:
            try:
                downloaded_size = temp_file.tell()
                if downloaded_size > 0:
                    get_headers['Range'] = 'bytes=%d-' % downloaded_size
                r = requests.get(url, headers=get_headers, stream=True,
                                 cookies=cookies, timeout=API_FILE_DOWNLOAD_TIMEOUT)
                r.raise_for_status()
                accept_ranges = r.headers.get('Accept-Ranges')
                content_length = r.headers.get('Content-Length')
                if accept_ranges == 'bytes':
                    if downloaded_size == 0:
                        total_content_length = int(content_length) if content_length is not None else None
                else:
                    if downloaded_size > 0:
                        temp_file.truncate(0)
                        downloaded_size = temp_file.tell()
                    total_content_length = int(content_length) if content_length is not None else None

                progress = tqdm(
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    total=total_content_length,
                    initial=downloaded_size,
                    desc="Downloading {}".format(file_name),
                )
                for chunk in r.iter_content(chunk_size=API_FILE_DOWNLOAD_CHUNK_SIZE):
                    if chunk:
                        progress.update(len(chunk))
                        temp_file.write(chunk)
                progress.close()
                break
            except Exception as e:
                retry = retry.increment('GET', url, error=e)
                retry.sleep()

    downloaded_length = os.path.getsize(temp_file.name)
    if total_content_length != downloaded_length:
        os.remove(temp_file.name)
        msg = 'File %s download incomplete, content_length: %s but the file downloaded length: %s, please download again' % (
            file_name, total_content_length, downloaded_length)
        raise FileDownloadError(msg)
    # fix folder recursive issue
    os.makedirs(os.path.dirname(os.path.join(local_dir, file_name)), exist_ok=True)
    os.replace(temp_file.name, os.path.join(local_dir, file_name))
    return


if __name__ == '__main__':
    token = "your_access_token"

    url = "https://hub.opencsg.com/api/v1/models/wayne0019/lwfmodel/resolve/lfsfile.bin"
    local_dir = '/home/test/'
    file_name = 'test.txt'
    headers = None
    cookies = None
    http_get(url=url,
             token=token,
             local_dir=local_dir,
             file_name=file_name,
             headers=headers,
             cookies=cookies)
