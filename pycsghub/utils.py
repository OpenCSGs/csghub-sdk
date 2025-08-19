import hashlib
import os
import pickle
import shutil
import tempfile
import urllib
from pathlib import Path
from typing import Optional, Union, Dict, Any
from urllib.parse import quote, urlparse
import logging

import requests
from huggingface_hub.hf_api import ModelInfo, DatasetInfo, SpaceInfo

from pycsghub._token import _get_token_from_file, _get_token_from_environment
from pycsghub.constants import MODEL_ID_SEPARATOR, DEFAULT_CSG_GROUP, DEFAULT_CSGHUB_DOMAIN
from pycsghub.constants import OPERATION_ACTION_API, OPERATION_ACTION_GIT
from pycsghub.constants import REPO_SOURCE_CSG, REPO_SOURCE_HF, REPO_SOURCE_MS
from pycsghub.constants import REPO_TYPE_MODEL, REPO_TYPE_DATASET, REPO_TYPE_SPACE
from pycsghub.constants import S3_INTERNAL
from pycsghub.errors import FileIntegrityError

import re

logger = logging.getLogger(__name__)

def get_session() -> requests.Session:
    session = requests.Session()
    # if constants.HF_HUB_OFFLINE:
    #     session.mount("http://", OfflineAdapter())
    #     session.mount("https://", OfflineAdapter())
    # else:
    #     session.mount("http://", UniqueRequestIdAdapter())
    #     session.mount("https://", UniqueRequestIdAdapter())
    return session


def get_token_to_send(token: Optional[str] = None) -> Optional[str]:
    """Get token to send
    
    Priority:
    1. Explicitly provided token parameter
    2. Environment variable CSGHUB_TOKEN
    3. Configuration file ~/.csghub/token
    """
    if token:
        return token
    
    # Check environment variable
    env_token = os.environ.get("CSGHUB_TOKEN")
    if env_token:
        return env_token
    
    # Check configuration file
    try:
        from pycsghub._token import _get_token_from_file
        file_token = _get_token_from_file()
        if file_token:
            return file_token
    except Exception:
        pass
    
    return None


def _validate_token_to_send():
    pass


def build_csg_headers(token: Optional[str] = None, headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build CSG request headers"""
    default_headers = {
        "User-Agent": "csghub-sdk",
        "Accept": "application/json",
    }
    
    if token:
        default_headers["Authorization"] = f"Bearer {token}"
    
    if headers:
        default_headers.update(headers)
    
    return default_headers


def model_id_to_group_owner_name(model_id: str):
    """Convert repo ID to group and owner name"""
    if "/" not in model_id:
        raise ValueError(f"Invalid repo_id format: {model_id}")
    
    parts = model_id.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid repo_id format: {model_id}")
    
    namespace, name = parts
    return namespace, name


def validate_cache_directory(cache_dir: str) -> bool:
    """Validate cache directory is available
    
    Args:
        cache_dir (str): cache directory path
        
    Returns:
        bool: cache directory is available
    """
    try:
        # Windows path length check
        if os.name == 'nt':
            # Windows has 260 character path limit, need to reserve space
            if len(os.path.abspath(cache_dir)) > 240:
                print(f"Warning: Cache directory path too long for Windows: {cache_dir}")
                return False

        # Check if directory exists, if not, create it
        os.makedirs(cache_dir, exist_ok=True)

        # Check write permission
        test_file = os.path.join(cache_dir, '.test_write')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)

        # Check disk space (at least 100MB)
        free_space = shutil.disk_usage(cache_dir).free
        if free_space < 1024 * 1024 * 100:  # 100MB
            print(f"Warning: Low disk space in cache directory {cache_dir}")
            return False

        return True
    except (OSError, IOError) as e:
        print(f"Warning: Cache directory validation failed for {cache_dir}: {e}")
        return False


def cleanup_cache_directory(cache_dir: str) -> bool:
    """Clean corrupted cache files
    
    Args:
        cache_dir (str): cache directory path
        
    Returns:
        bool: clean cache directory successfully
    """
    try:
        # Clean corrupted index files
        index_file = os.path.join(cache_dir, '.msc')
        if os.path.exists(index_file):
            try:
                with open(index_file, 'rb') as f:
                    pickle.load(f)
            except (pickle.PickleError, EOFError, IOError):
                print(f"Warning: Removing corrupted cache index file: {index_file}")
                os.remove(index_file)

        # Clean temporary files
        for root, dirs, files in os.walk(cache_dir):
            for file in files:
                if file.endswith('.tmp') or file.startswith('.test_'):
                    try:
                        os.remove(os.path.join(root, file))
                    except OSError:
                        pass

        # Clean empty directories
        for root, dirs, files in os.walk(cache_dir, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):  # directory is empty
                        os.rmdir(dir_path)
                except OSError:
                    pass

        return True
    except Exception as e:
        print(f"Warning: Cache cleanup failed for {cache_dir}: {e}")
        return False


def sanitize_path_for_windows(path: str) -> str:
    """Clean path, make it available in Windows
    
    Args:
        path (str): original path
        
    Returns:
        str: cleaned path
    """
    if os.name == 'nt':
        # Windows forbidden characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            path = path.replace(char, '_')

        # Handle Windows path length limit
        if len(path) > 240:
            # Use short path or truncate
            try:
                import win32api
                short_path = win32api.GetShortPathName(path)
                if len(short_path) <= 240:
                    return short_path
            except ImportError:
                pass

            # Truncate path
            parts = path.split(os.sep)
            while len(path) > 240 and len(parts) > 1:
                parts.pop(1)  # Keep root directory
                path = os.sep.join(parts)

    return path


def get_cache_dir_with_fallback(model_id: Optional[str] = None, repo_type: Optional[str] = None) -> str:
    """Get cache directory, if failed, use fallback
    
    Args:
        model_id (str, optional): model ID
        repo_type (str, optional): repository type
        
    Returns:
        str: available cache directory path
    """
    # Get primary cache directory
    primary_cache = get_cache_dir(model_id, repo_type)

    # Clean path in Windows
    if os.name == 'nt':
        primary_cache = sanitize_path_for_windows(primary_cache)

    # Validate primary cache directory
    if validate_cache_directory(primary_cache):
        return primary_cache

    # Clean cache directory
    cleanup_cache_directory(primary_cache)

    # Validate again
    if validate_cache_directory(primary_cache):
        return primary_cache

    # Use temporary directory as fallback
    fallback_cache = os.path.join(tempfile.gettempdir(), 'csg_cache')
    if model_id:
        # Handle special characters in model ID in Windows
        safe_model_id = model_id.replace('/', '_').replace('\\', '_')
        fallback_cache = os.path.join(fallback_cache, safe_model_id)

    try:
        os.makedirs(fallback_cache, exist_ok=True)
        print(f"Warning: Using fallback cache directory: {fallback_cache}")
        return fallback_cache
    except OSError as e:
        print(f"Error: Cannot create fallback cache directory: {e}")
        # Last fallback: use current directory
        current_cache = os.path.join(os.getcwd(), '.csg_cache')
        if model_id:
            safe_model_id = model_id.replace('/', '_').replace('\\', '_')
            current_cache = os.path.join(current_cache, safe_model_id)
        os.makedirs(current_cache, exist_ok=True)
        print(f"Warning: Using current directory cache: {current_cache}")
        return current_cache


def get_cache_dir(model_id: Optional[str] = None, repo_type: Optional[str] = None) -> Union[str, Path]:
    """cache dir precedence:
        function parameter > environment > current directory

    Args:
        model_id (str, optional): The model id.
        repo_type (str, optional): The repo type

    Returns:
        str: the model_id dir if model_id not None, otherwise cache root dir.
    """
    default_cache_dir = get_default_cache_dir()
    sub_dir = 'hub'
    if repo_type == REPO_TYPE_DATASET:
        sub_dir = 'dataset'
    base_path = os.getenv('CSGHUB_CACHE', os.path.join(default_cache_dir, sub_dir))
    return base_path if model_id is None else os.path.join(
        base_path, model_id + '/')


def get_default_cache_dir() -> Path:
    """
    default base dir: current directory
    """
    default_cache_dir = Path.cwd()
    return default_cache_dir


def get_model_temp_dir(cache_dir: str, model_id: str) -> str:
    # Parse model ID
    if '/' in model_id:
        owner, name = model_id.split('/', 1)
    else:
        owner = DEFAULT_CSG_GROUP
        name = model_id

    # Handle special characters in Windows
    if os.name == 'nt':
        # Replace Windows forbidden characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            owner = owner.replace(char, '_')
            name = name.replace(char, '_')

    model_cache_dir = os.path.join(cache_dir, owner, name)

    # Check path length in Windows
    if os.name == 'nt' and len(os.path.abspath(model_cache_dir)) > 240:
        # Use system temporary directory as fallback
        fallback_temp = os.path.join(tempfile.gettempdir(), f'csg_temp_{owner}_{name}')
        try:
            os.makedirs(fallback_temp, exist_ok=True)
            return fallback_temp
        except OSError as e:
            print(f"Warning: Cannot create fallback temp directory {fallback_temp}: {e}")
            # Last fallback: use current directory
            current_temp = os.path.join(os.getcwd(), f'.csg_temp_{owner}_{name}')
            os.makedirs(current_temp, exist_ok=True)
            return current_temp

    try:
        os.makedirs(model_cache_dir, exist_ok=True)
        return model_cache_dir
    except OSError as e:
        print(f"Warning: Cannot create model temp directory {model_cache_dir}: {e}")
        # Use system temporary directory as fallback
        fallback_temp = os.path.join(tempfile.gettempdir(), f'csg_temp_{owner}_{name}')
        os.makedirs(fallback_temp, exist_ok=True)
        return fallback_temp


def get_repo_info(
        repo_id: str,
        *,
        revision: Optional[str] = None,
        repo_type: Optional[str] = None,
        timeout: Optional[float] = None,
        files_metadata: bool = False,
        token: Union[bool, str, None] = None,
        endpoint: Optional[str] = None,
        source: Optional[str] = None,
) -> Union[ModelInfo, DatasetInfo, SpaceInfo]:
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
    if repo_type is None or repo_type == REPO_TYPE_MODEL:
        method = model_info
    elif repo_type == REPO_TYPE_DATASET:
        method = dataset_info
    elif repo_type == REPO_TYPE_SPACE:
        method = space_info
    else:
        raise ValueError("Unsupported repo type.")
    return method(
        repo_id,
        revision=revision,
        token=token,
        timeout=timeout,
        files_metadata=files_metadata,
        endpoint=endpoint,
        source=source,
    )


def dataset_info(
        repo_id: str,
        *,
        revision: Optional[str] = None,
        timeout: Optional[float] = None,
        files_metadata: bool = False,
        token: Union[bool, str, None] = None,
        endpoint: Optional[str] = None,
        source: Optional[str] = None,
) -> DatasetInfo:
    """
    Get info on one specific dataset on opencsg.com.

    Dataset can be private if you pass an acceptable token.

    Args:
        repo_id (`str`):
            A namespace (user or an organization) and a repo name separated
            by a `/`.
        revision (`str`, *optional*):
            The revision of the dataset repository from which to get the
            information.
        timeout (`float`, *optional*):
            Whether to set a timeout for the request to the Hub.
        files_metadata (`bool`, *optional*):
            Whether or not to retrieve metadata for files in the repository
            (size, LFS metadata, etc). Defaults to `False`.
        token (Union[bool, str, None], optional):
            A valid user access token (string). Defaults to the locally saved
            token, which is the recommended method for authentication.
            To disable authentication, pass `False`.

    Returns:
        [`hf_api.DatasetInfo`]: The dataset repository information.

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
    path = get_repo_meta_path(repo_type=REPO_TYPE_DATASET,
                              repo_id=repo_id,
                              revision=revision,
                              endpoint=endpoint,
                              source=source)
    params = {}
    if files_metadata:
        params["blobs"] = True
    r = requests.get(path, headers=headers, timeout=timeout, params=params)
    if r.status_code != 200:
        logger.error(f"get {REPO_TYPE_DATASET} meta info from {path} response: {r.text}")
    r.raise_for_status()
    data = r.json()
    return DatasetInfo(**data)


def space_info(
        repo_id: str,
        *,
        revision: Optional[str] = None,
        timeout: Optional[float] = None,
        files_metadata: bool = False,
        token: Union[bool, str, None] = None,
        endpoint: Optional[str] = None,
        source: Optional[str] = None,
) -> SpaceInfo:
    """
    Get info on one specific space on opencsg.com.

    Space can be private if you pass an acceptable token.

    Args:
        repo_id (`str`):
            A namespace (user or an organization) and a repo name separated
            by a `/`.
        revision (`str`, *optional*):
            The revision of the space repository from which to get the
            information.
        timeout (`float`, *optional*):
            Whether to set a timeout for the request to the Hub.
        files_metadata (`bool`, *optional*):
            Whether or not to retrieve metadata for files in the repository
            (size, LFS metadata, etc). Defaults to `False`.
        token (Union[bool, str, None], optional):
            A valid user access token (string). Defaults to the locally saved
            token, which is the recommended method for authentication.
            To disable authentication, pass `False`.

    Returns:
        [`~hf_api.SpaceInfo`]: The space repository information.

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
    path = get_repo_meta_path(repo_type=REPO_TYPE_SPACE,
                              repo_id=repo_id,
                              revision=revision,
                              endpoint=endpoint,
                              source=source)
    params = {}
    if files_metadata:
        params["blobs"] = True
    r = requests.get(path, headers=headers, timeout=timeout, params=params)
    if r.status_code != 200:
        logger.error(f"get {REPO_TYPE_SPACE} meta info from {path} response: {r.text}")
    r.raise_for_status()
    data = r.json()
    return SpaceInfo(**data)


def model_info(
        repo_id: str,
        *,
        revision: Optional[str] = None,
        timeout: Optional[float] = None,
        securityStatus: Optional[bool] = None,
        files_metadata: bool = False,
        token: Union[bool, str, None] = None,
        endpoint: Optional[str] = None,
        source: Optional[str] = None,
) -> ModelInfo:
    """
    Note: It is a huggingface method moved here to adjust csghub server response.
    Get info on one specific model on opencsg.com

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
    path = get_repo_meta_path(repo_type=REPO_TYPE_MODEL,
                              repo_id=repo_id,
                              revision=revision,
                              endpoint=endpoint,
                              source=source)
    params = {}
    if securityStatus:
        params["securityStatus"] = True
    if files_metadata:
        params["blobs"] = True
    r = requests.get(path, headers=headers, timeout=timeout, params=params)
    if r.status_code != 200:
        logger.error(f"get {REPO_TYPE_MODEL} meta info from {path} response: {r.text}")
    r.raise_for_status()
    data = r.json()
    return ModelInfo(**data)


def get_repo_meta_path(
        repo_type: str,
        repo_id: str,
        revision: Optional[str] = None,
        endpoint: Optional[str] = None,
        source: Optional[str] = None,
) -> str:
    if repo_type != REPO_TYPE_MODEL and repo_type != REPO_TYPE_DATASET and repo_type != REPO_TYPE_SPACE:
        raise ValueError("repo_type must be one of 'model', 'dataset' or 'space'")

    if source != REPO_SOURCE_CSG and source != REPO_SOURCE_HF and source != REPO_SOURCE_MS and source is not None:
        raise ValueError("source must be one of 'csg', 'hf' or 'ms'")

    src_prefix = REPO_SOURCE_CSG if source is None else source
    path = (
        f"{endpoint}/{src_prefix}/api/{repo_type}s/{repo_id}/revision/main"
        if revision is None
        else f"{endpoint}/{src_prefix}/api/{repo_type}s/{repo_id}/revision/{quote(revision, safe='')}"
    )
    return path


def get_file_download_url(
        model_id: str,
        file_path: str,
        revision: str,
        repo_type: Optional[str] = None,
        endpoint: Optional[str] = None,
        source: Optional[str] = None,
) -> str:
    """Format file download url according to `model_id`, `revision` and `file_path`.
    Args:
        model_id (str): The model_id.
        file_path (str): File path
        revision (str): File revision.

    Returns:
        str: The file url.
    """
    file_path = urllib.parse.quote(file_path)
    revision = urllib.parse.quote(revision)
    src_prefix = REPO_SOURCE_CSG if source is None else source

    download_url_template = '{endpoint}/{src_prefix}/{model_id}/resolve/{revision}/{file_path}'
    if repo_type == REPO_TYPE_DATASET:
        download_url_template = '{endpoint}/{src_prefix}/datasets/{model_id}/resolve/{revision}/{file_path}'
    elif repo_type == REPO_TYPE_SPACE:
        download_url_template = '{endpoint}/{src_prefix}/spaces/{model_id}/resolve/{revision}/{file_path}'

    return download_url_template.format(
        endpoint=endpoint,
        src_prefix=src_prefix,
        model_id=model_id,
        revision=revision,
        file_path=file_path,
    )


def get_endpoint(endpoint: Optional[str] = None, operation: Optional[str] = OPERATION_ACTION_API) -> str:
    """Format endpoint to remove trailing slash and add a leading slash if not present.
    Args:
        endpoint (str): The endpoint url.

    Returns:
        str: The formatted endpoint url.
    """

    env_csghub_domain = os.getenv('CSGHUB_DOMAIN', None)
    correct_endpoint = None
    if bool(endpoint) and endpoint != DEFAULT_CSGHUB_DOMAIN:
        correct_endpoint = endpoint
    elif bool(env_csghub_domain) and env_csghub_domain != DEFAULT_CSGHUB_DOMAIN:
        correct_endpoint = env_csghub_domain
    else:
        correct_endpoint = DEFAULT_CSGHUB_DOMAIN

    if operation == OPERATION_ACTION_GIT:
        scheme = urlparse(correct_endpoint).scheme
        correct_endpoint = correct_endpoint.replace(f"{scheme}://hub.", f"{scheme}://")
    if correct_endpoint.endswith('/'):
        correct_endpoint = correct_endpoint[:-1]
    return correct_endpoint


def file_integrity_validation(file_path,
                              expected_sha256) -> None:
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


def compute_hash(file_path) -> str:
    BUFFER_SIZE = 1024 * 64  # 64k buffer size
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            sha256_hash.update(data)
    return sha256_hash.hexdigest()


def pack_repo_file_info(repo_file_path,
                        revision) -> Dict[str, str]:
    repo_file_info = {'Path': repo_file_path,
                      'Revision': revision}
    return repo_file_info


def contains_chinese(text: str) -> bool:
    """
    Check if the string contains Chinese characters
    
    Args:
        text: The string to check
        
    Returns:
        bool: If the string contains Chinese characters, return True, otherwise return False
    """
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    return bool(chinese_pattern.search(text))


def validate_repo_id(repo_id: str) -> None:
    """
    Validate if the repository ID contains Chinese characters
    
    Args:
        repo_id: The repository ID
        
    Raises:
        ValueError: If the repository ID contains Chinese characters
    """
    if contains_chinese(repo_id):
        raise ValueError(
            f"❌ Error: Repository ID '{repo_id}' contains Chinese characters. "
            f"Repository names cannot contain Chinese characters. "
            f"Please use only English letters, numbers, hyphens, and underscores."
        )
