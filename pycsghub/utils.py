from typing import Optional, Union, Dict

from pathlib import Path
import os
from pycsghub.constants import MODEL_ID_SEPARATOR, DEFAULT_CSG_GROUP, DEFAULT_CSGHUB_DOMAIN
import requests
from huggingface_hub.hf_api import ModelInfo
import urllib
import hashlib
from pycsghub.errors import FileIntegrityError
from pycsghub._token import _get_token_from_file, _get_token_from_environment
from urllib.parse import quote


def get_session():
    session = requests.Session()
    # if constants.HF_HUB_OFFLINE:
    #     session.mount("http://", OfflineAdapter())
    #     session.mount("https://", OfflineAdapter())
    # else:
    #     session.mount("http://", UniqueRequestIdAdapter())
    #     session.mount("https://", UniqueRequestIdAdapter())
    return session


def get_token_to_send(token):
    if token:
        return token
    else:
        return _get_token_from_environment() or _get_token_from_file()


def _validate_token_to_send():
    pass


def build_csg_headers(
    *,
    token: Optional[Union[bool, str]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    # Get auth token to send
    token_to_send = get_token_to_send(token)
    csg_headers = {}
    # Combine headers
    if token_to_send is not None:
        csg_headers["authorization"] = f"Bearer {token_to_send}"
    if headers is not None:
        csg_headers.update(headers)
    return csg_headers


def model_id_to_group_owner_name(model_id: str):
    if MODEL_ID_SEPARATOR in model_id:
        group_or_owner = model_id.split(MODEL_ID_SEPARATOR)[0]
        name = model_id.split(MODEL_ID_SEPARATOR)[1]
    else:
        group_or_owner = DEFAULT_CSG_GROUP
        name = model_id
    return group_or_owner, name


def get_cache_dir(model_id: Optional[str] = None):
    """cache dir precedence:
        function parameter > environment > ~/.cache/csg/hub

    Args:
        model_id (str, optional): The model id.

    Returns:
        str: the model_id dir if model_id not None, otherwise cache root dir.
    """
    default_cache_dir = get_default_cache_dir()
    base_path = os.getenv('CSGHUB_CACHE',
                          os.path.join(default_cache_dir, 'hub'))
    return base_path if model_id is None else os.path.join(
        base_path, model_id + '/')


def get_default_cache_dir():
    """
    default base dir: '~/.cache/csg'
    """
    default_cache_dir = Path.home().joinpath('.cache', 'csg')
    return default_cache_dir


def get_repo_info(
    repo_id: str,
    *,
    revision: Optional[str] = None,
    repo_type: Optional[str] = None,
    timeout: Optional[float] = None,
    files_metadata: bool = False,
    token: Union[bool, str, None] = None,
    endpoint: Optional[str] = None
):
    """
    Get the info object for a given repo of a given type.

    Args:
        repo_id (`str`):
            A namespace (user or an organization) and a repo name separated
            by a `/`.
        revision (`str`, *optional*):
            The revision of the repository from which to get the
            information.
        repo_type (`str`, *optional*):
            Set to `"dataset"` or `"space"` if getting repository info from a dataset or a space,
            `None` or `"model"` if getting repository info from a model. Default is `None`.
        timeout (`float`, *optional*):
            Whether to set a timeout for the request to the Hub.
        files_metadata (`bool`, *optional*):
            Whether or not to retrieve metadata for files in the repository
            (size, LFS metadata, etc). Defaults to `False`.
        token (Union[bool, str, None], optional):
            A valid user access token (string). Defaults to the locally saved
            token.

    Returns:
        `Union[SpaceInfo, DatasetInfo, ModelInfo]`: The repository information, as a
        [`huggingface_hub.hf_api.DatasetInfo`], [`huggingface_hub.hf_api.ModelInfo`]
        or [`huggingface_hub.hf_api.SpaceInfo`] object.

    <Tip>

    Raises the following errors:

        - [`~utils.RepositoryNotFoundError`]
          If the repository to download from cannot be found. This may be because it doesn't exist,
          or because it is set to `private` and you do not have access.
        - [`~utils.RevisionNotFoundError`]
          If the revision to download from cannot be found.

    </Tip>
    """
    if repo_type is None or repo_type == "model":
        method = model_info
    # todo dataset and spaceset are now not supported
    else:
        raise ValueError("Unsupported repo type.")
    return method(
        repo_id,
        revision=revision,
        token=token,
        timeout=timeout,
        files_metadata=files_metadata,
        endpoint=endpoint
    )


def model_info(
    repo_id: str,
    *,
    revision: Optional[str] = None,
    timeout: Optional[float] = None,
    securityStatus: Optional[bool] = None,
    files_metadata: bool = False,
    token: Union[bool, str, None] = None,
    endpoint: Optional[str] = None
) -> ModelInfo:
    """
    Note: It is a huggingface method moved here to adjust csghub server response.

    Get info on one specific model on huggingface.co

    Model can be private if you pass an acceptable token or are logged in.

    Args:
        repo_id (`str`):
            A namespace (user or an organization) and a repo name separated
            by a `/`.
        revision (`str`, *optional*):
            The revision of the model repository from which to get the
            information.
        timeout (`float`, *optional*):
            Whether to set a timeout for the request to the Hub.
        securityStatus (`bool`, *optional*):
            Whether to retrieve the security status from the model
            repository as well.
        files_metadata (`bool`, *optional*):
            Whether or not to retrieve metadata for files in the repository
            (size, LFS metadata, etc). Defaults to `False`.
        token (Union[bool, str, None], optional):
            A valid user access token (string). Used to build csghub server request
            header.

    Returns:
        [`huggingface_hub.hf_api.ModelInfo`]: The model repository information.

    <Tip>

    Raises the following errors:

        - [`~utils.RepositoryNotFoundError`]
          If the repository to download from cannot be found. This may be because it doesn't exist,
          or because it is set to `private` and you do not have access.
        - [`~utils.RevisionNotFoundError`]
          If the revision to download from cannot be found.

    </Tip>
    """
    headers = build_csg_headers(token=token)
    path = (
        f"{endpoint}/hf/api/models/{repo_id}/revision/main"
        if revision is None
        else f"{endpoint}/hf/api/models/{repo_id}/revision/{quote(revision, safe='')}"
    )
    params = {}
    if securityStatus:
        params["securityStatus"] = True
    if files_metadata:
        params["blobs"] = True
    r = requests.get(path,
                     headers=headers,
                     timeout=timeout,
                     params=params)
    r.raise_for_status()
    data = r.json()
    return ModelInfo(**data)


def get_endpoint():
    csghub_domain = os.getenv('CSGHUB_DOMAIN',
                              DEFAULT_CSGHUB_DOMAIN)
    return csghub_domain


def get_file_download_url(model_id: str, file_path: str, revision: str):
    """Format file download url according to `model_id`, `revision` and `file_path`.
    Args:
        model_id (str): The model_id.
        file_path (str): File path
        revision (str): File revision.

    Returns:
        str: The file url.
    """
    file_path = urllib.parse.quote_plus(file_path)
    revision = urllib.parse.quote_plus(revision)
    download_url_template = '{endpoint}/hf/{model_id}/resolve/{revision}/{file_path}'
    return download_url_template.format(
        endpoint=get_endpoint(),
        model_id=model_id,
        revision=revision,
        file_path=file_path,
    )


def file_integrity_validation(file_path, expected_sha256):
    """Validate the file hash is expected, if not, delete the file

    Args:
        file_path (str): The file to validate
        expected_sha256 (str): The expected sha256 hash

    Raises:
        FileIntegrityError: If file_path hash is not expected.

    """
    file_sha256 = compute_hash(file_path)
    if not file_sha256 == expected_sha256:
        os.remove(file_path)
        msg = 'File %s integrity check failed, the download may be incomplete, please try again.' % file_path
        raise FileIntegrityError(msg)


def compute_hash(file_path):
    BUFFER_SIZE = 1024 * 64  # 64k buffer size
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            sha256_hash.update(data)
    return sha256_hash.hexdigest()


def pack_model_file_info(model_file_path,
                         revision):
    model_file_info = {'Path': model_file_path,
                       'Revision': revision}
    return model_file_info
