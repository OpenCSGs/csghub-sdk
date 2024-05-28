import tempfile
from functools import partial
from http.cookiejar import CookieJar

import requests
from requests.adapters import Retry
from tqdm import tqdm
from pycsghub.utils import build_csg_headers
from pycsghub.constants import API_FILE_DOWNLOAD_RETRY_TIMES, API_FILE_DOWNLOAD_TIMEOUT, API_FILE_DOWNLOAD_CHUNK_SIZE
from pycsghub.errors import FileDownloadError
import os


def try_to_load_from_cache():
    pass


def cached_download():
    pass


def csg_hub_download():
    pass


def get_csg_hub_url():
    pass


def http_get(*,
             url: str,
             local_dir: str,
             file_name: str,
             headers: dict = None,
             cookies: CookieJar = None,
             token: str = None):
    '''
    下载核心API，通过request的方式直接拉取对象到本地的临时文件
    :param token:
    :param url:
    :param local_dir:
    :param file_name:
    :param headers:
    :param cookies:
    :return:
    '''
    tempfile_mgr = partial(tempfile.NamedTemporaryFile,
                           mode='wb',
                           dir=local_dir,
                           delete=False)
    get_headers = build_csg_headers(token=token,
                                    headers=headers)
    with tempfile_mgr() as temp_file:
        # retry sleep 0.5s, 1s, 2s, 4s
        retry = Retry(
            total=API_FILE_DOWNLOAD_RETRY_TIMES,
            backoff_factor=1,
            allowed_methods=['GET'])
        while True:
            try:
                downloaded_size = temp_file.tell()
                # get_headers['Range'] = 'bytes=%d-' % downloaded_size #todo 暂时先不放
                r = requests.get(url,
                                 headers=get_headers,
                                 stream=True,
                                 cookies=cookies,
                                 timeout=API_FILE_DOWNLOAD_TIMEOUT)

                r.raise_for_status()
                content_length = r.headers.get('Content-Length')
                total = int(
                    content_length) if content_length is not None else None

                progress = tqdm(
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    total=total,
                    initial=downloaded_size,
                    desc="Downloading {}".format(file_name),
                )
                for chunk in r.iter_content(
                        chunk_size=API_FILE_DOWNLOAD_CHUNK_SIZE):
                    if chunk:  # filter out keep-alive new chunks
                        progress.update(len(chunk))
                        temp_file.write(chunk)
                progress.close()
                break
            except Exception as e:  # no matter what happen, we will retry.
                retry = retry.increment('GET', url, error=e)
                retry.sleep()

    #logger.debug('storing %s in cache at %s', url, local_dir)
    downloaded_length = os.path.getsize(temp_file.name)
    if total != downloaded_length:
        os.remove(temp_file.name)
        msg = 'File %s download incomplete, content_length: %s but the \
                            file downloaded length: %s, please download again' % (
            file_name, total, downloaded_length)
        #logger.error(msg)
        raise FileDownloadError(msg)
    os.replace(temp_file.name, os.path.join(local_dir, file_name))
    return


if __name__ == '__main__':
    token = "f3a7b9c1d6e5f8e2a1b5d4f9e6a2b8d7c3a4e2b1d9f6e7a8d2c5a7b4c1e3f5b8a1d4f9" + \
            "b7d6e2f8a5d3b1e7f9c6a8b2d1e4f7d5b6e9f2a4b3c8e1d7f995hd82hf"

    url = "https://hub-stg.opencsg.com/api/v1/models/wayne0019/lwfmodel/resolve/lfsfile.bin"
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






