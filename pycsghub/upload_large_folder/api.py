from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
    overload,
)
import json
import warnings
from urllib.parse import quote
from . import logging
from enum import Enum
from .. import (constants)
from ._commit_api import (
    CommitOperation,
    CommitOperationAdd,
    CommitOperationCopy
)
from dataclasses import dataclass, field
from concurrent.futures import Future, ThreadPoolExecutor

logger = logging.get_logger(__name__)

class RepoUrl(str):
    """Subclass of `str` describing a repo URL on the Hub.

    `RepoUrl` is returned by `HfApi.create_repo`. It inherits from `str` for backward
    compatibility. At initialization, the URL is parsed to populate properties:
    - endpoint (`str`)
    - namespace (`Optional[str]`)
    - repo_name (`str`)
    - repo_id (`str`)
    - repo_type (`Literal["model", "dataset", "space"]`)
    - url (`str`)

    Args:
        url (`Any`):
            String value of the repo url.
        endpoint (`str`, *optional*):
            Endpoint of the Hub. Defaults to <https://huggingface.co>.

    Example:
    ```py
    >>> RepoUrl('https://huggingface.co/gpt2')
    RepoUrl('https://huggingface.co/gpt2', endpoint='https://huggingface.co', repo_type='model', repo_id='gpt2')

    >>> RepoUrl('https://hub-ci.huggingface.co/datasets/dummy_user/dummy_dataset', endpoint='https://hub-ci.huggingface.co')
    RepoUrl('https://hub-ci.huggingface.co/datasets/dummy_user/dummy_dataset', endpoint='https://hub-ci.huggingface.co', repo_type='dataset', repo_id='dummy_user/dummy_dataset')

    >>> RepoUrl('hf://datasets/my-user/my-dataset')
    RepoUrl('hf://datasets/my-user/my-dataset', endpoint='https://huggingface.co', repo_type='dataset', repo_id='user/dataset')

    >>> HfApi.create_repo("dummy_model")
    RepoUrl('https://huggingface.co/Wauplin/dummy_model', endpoint='https://huggingface.co', repo_type='model', repo_id='Wauplin/dummy_model')
    ```

    Raises:
        [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
            If URL cannot be parsed.
        [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
            If `repo_type` is unknown.
    """

    def __new__(cls, url: Any, endpoint: Optional[str] = None):
        # url = fix_hf_endpoint_in_url(url, endpoint=endpoint)
        url = ""
        return super(RepoUrl, cls).__new__(cls, url)

    def __init__(self, url: Any, endpoint: Optional[str] = None) -> None:
        super().__init__()
        # Parse URL
        # self.endpoint = endpoint or constants.ENDPOINT
        # repo_type, namespace, repo_name = repo_type_and_id_from_hf_id(self, hub_url=self.endpoint)
        repo_type, namespace, repo_name = ""

        # Populate fields
        self.namespace = namespace
        self.repo_name = repo_name
        self.repo_id = repo_name if namespace is None else f"{namespace}/{repo_name}"
        self.repo_type = repo_type or constants.REPO_TYPE_MODEL
        # self.repo_type = repo_type or REPO_TYPE_MODEL
        self.url = str(self)  # just in case it's needed

    def __repr__(self) -> str:
        return f"RepoUrl('{self}', endpoint='{self.endpoint}', repo_type='{self.repo_type}', repo_id='{self.repo_id}')"

class SpaceHardware(str, Enum):
    """
    Enumeration of hardwares available to run your Space on the Hub.

    Value can be compared to a string:
    ```py
    assert SpaceHardware.CPU_BASIC == "cpu-basic"
    ```

    Taken from https://github.com/huggingface/moon-landing/blob/main/server/repo_types/SpaceInfo.ts#L73 (private url).
    """

    CPU_BASIC = "cpu-basic"
    CPU_UPGRADE = "cpu-upgrade"
    T4_SMALL = "t4-small"
    T4_MEDIUM = "t4-medium"
    L4X1 = "l4x1"
    L4X4 = "l4x4"
    ZERO_A10G = "zero-a10g"
    A10G_SMALL = "a10g-small"
    A10G_LARGE = "a10g-large"
    A10G_LARGEX2 = "a10g-largex2"
    A10G_LARGEX4 = "a10g-largex4"
    A100_LARGE = "a100-large"
    V5E_1X1 = "v5e-1x1"
    V5E_2X2 = "v5e-2x2"
    V5E_2X4 = "v5e-2x4"


class SpaceStorage(str, Enum):
    """
    Enumeration of persistent storage available for your Space on the Hub.

    Value can be compared to a string:
    ```py
    assert SpaceStorage.SMALL == "small"
    ```

    Taken from https://github.com/huggingface/moon-landing/blob/main/server/repo_types/SpaceHardwareFlavor.ts#L24 (private url).
    """

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

@dataclass
class CommitInfo(str):
    """Data structure containing information about a newly created commit.

    Returned by any method that creates a commit on the Hub: [`create_commit`], [`upload_file`], [`upload_folder`],
    [`delete_file`], [`delete_folder`]. It inherits from `str` for backward compatibility but using methods specific
    to `str` is deprecated.

    Attributes:
        commit_url (`str`):
            Url where to find the commit.

        commit_message (`str`):
            The summary (first line) of the commit that has been created.

        commit_description (`str`):
            Description of the commit that has been created. Can be empty.

        oid (`str`):
            Commit hash id. Example: `"91c54ad1727ee830252e457677f467be0bfd8a57"`.

        pr_url (`str`, *optional*):
            Url to the PR that has been created, if any. Populated when `create_pr=True`
            is passed.

        pr_revision (`str`, *optional*):
            Revision of the PR that has been created, if any. Populated when
            `create_pr=True` is passed. Example: `"refs/pr/1"`.

        pr_num (`int`, *optional*):
            Number of the PR discussion that has been created, if any. Populated when
            `create_pr=True` is passed. Can be passed as `discussion_num` in
            [`get_discussion_details`]. Example: `1`.

        repo_url (`RepoUrl`):
            Repo URL of the commit containing info like repo_id, repo_type, etc.

        _url (`str`, *optional*):
            Legacy url for `str` compatibility. Can be the url to the uploaded file on the Hub (if returned by
            [`upload_file`]), to the uploaded folder on the Hub (if returned by [`upload_folder`]) or to the commit on
            the Hub (if returned by [`create_commit`]). Defaults to `commit_url`. It is deprecated to use this
            attribute. Please use `commit_url` instead.
    """

    commit_url: str
    commit_message: str
    commit_description: str
    oid: str
    pr_url: Optional[str] = None

    # Computed from `commit_url` in `__post_init__`
    repo_url: RepoUrl = field(init=False)

    # Computed from `pr_url` in `__post_init__`
    pr_revision: Optional[str] = field(init=False)
    pr_num: Optional[str] = field(init=False)

    # legacy url for `str` compatibility (ex: url to uploaded file, url to uploaded folder, url to PR, etc.)
    _url: str = field(repr=False, default=None)  # type: ignore  # defaults to `commit_url`

    def __new__(cls, *args, commit_url: str, _url: Optional[str] = None, **kwargs):
        return str.__new__(cls, _url or commit_url)

    def __post_init__(self):
        """Populate pr-related fields after initialization.

        See https://docs.python.org/3.10/library/dataclasses.html#post-init-processing.
        """
        # Repo info
        self.repo_url = RepoUrl(self.commit_url.split("/commit/")[0])

        # PR info
        if self.pr_url is not None:
            # self.pr_revision = _parse_revision_from_pr_url(self.pr_url)
            self.pr_num = int(self.pr_revision.split("/")[-1])
        else:
            self.pr_revision = None
            self.pr_num = None



class HfApi:
    def _build_hf_headers(
        self,
        token: Union[bool, str, None] = None,
        library_name: Optional[str] = None,
        library_version: Optional[str] = None,
        user_agent: Union[Dict, str, None] = None,
    ) -> Dict[str, str]:
        """
        Alias for [`build_hf_headers`] that uses the token from [`HfApi`] client
        when `token` is not provided.
        """
        if token is None:
            # Cannot do `token = token or self.token` as token can be `False`.
            token = self.token
        return {}
        # return build_hf_headers(
        #     token=token,
        #     library_name=library_name or self.library_name,
        #     library_version=library_version or self.library_version,
        #     user_agent=user_agent or self.user_agent,
        #     headers=self.headers,
        # )

    
    def create_repo(
        self,
        repo_id: str,
        *,
        token: Union[str, bool, None] = None,
        private: Optional[bool] = None,
        repo_type: Optional[str] = None,
        exist_ok: bool = False,
        resource_group_id: Optional[str] = None,
        space_sdk: Optional[str] = None,
        space_hardware: Optional[SpaceHardware] = None,
        space_storage: Optional[SpaceStorage] = None,
        space_sleep_time: Optional[int] = None,
        space_secrets: Optional[List[Dict[str, str]]] = None,
        space_variables: Optional[List[Dict[str, str]]] = None,
    ) -> RepoUrl:
        """Create an empty repo on the HuggingFace Hub.

        Args:
            repo_id (`str`):
                A namespace (user or an organization) and a repo name separated
                by a `/`.
            token (Union[bool, str, None], optional):
                A valid user access token (string). Defaults to the locally saved
                token, which is the recommended method for authentication (see
                https://huggingface.co/docs/huggingface_hub/quick-start#authentication).
                To disable authentication, pass `False`.
            private (`bool`, *optional*):
                Whether to make the repo private. If `None` (default), the repo will be public unless the organization's default is private. This value is ignored if the repo already exists.
            repo_type (`str`, *optional*):
                Set to `"dataset"` or `"space"` if uploading to a dataset or
                space, `None` or `"model"` if uploading to a model. Default is
                `None`.
            exist_ok (`bool`, *optional*, defaults to `False`):
                If `True`, do not raise an error if repo already exists.
            resource_group_id (`str`, *optional*):
                Resource group in which to create the repo. Resource groups is only available for organizations and
                allow to define which members of the organization can access the resource. The ID of a resource group
                can be found in the URL of the resource's page on the Hub (e.g. `"66670e5163145ca562cb1988"`).
                To learn more about resource groups, see https://huggingface.co/docs/hub/en/security-resource-groups.
            space_sdk (`str`, *optional*):
                Choice of SDK to use if repo_type is "space". Can be "streamlit", "gradio", "docker", or "static".
            space_hardware (`SpaceHardware` or `str`, *optional*):
                Choice of Hardware if repo_type is "space". See [`SpaceHardware`] for a complete list.
            space_storage (`SpaceStorage` or `str`, *optional*):
                Choice of persistent storage tier. Example: `"small"`. See [`SpaceStorage`] for a complete list.
            space_sleep_time (`int`, *optional*):
                Number of seconds of inactivity to wait before a Space is put to sleep. Set to `-1` if you don't want
                your Space to sleep (default behavior for upgraded hardware). For free hardware, you can't configure
                the sleep time (value is fixed to 48 hours of inactivity).
                See https://huggingface.co/docs/hub/spaces-gpus#sleep-time for more details.
            space_secrets (`List[Dict[str, str]]`, *optional*):
                A list of secret keys to set in your Space. Each item is in the form `{"key": ..., "value": ..., "description": ...}` where description is optional.
                For more details, see https://huggingface.co/docs/hub/spaces-overview#managing-secrets.
            space_variables (`List[Dict[str, str]]`, *optional*):
                A list of public environment variables to set in your Space. Each item is in the form `{"key": ..., "value": ..., "description": ...}` where description is optional.
                For more details, see https://huggingface.co/docs/hub/spaces-overview#managing-secrets-and-environment-variables.

        Returns:
            [`RepoUrl`]: URL to the newly created repo. Value is a subclass of `str` containing
            attributes like `endpoint`, `repo_type` and `repo_id`.
        """
        organization, name = repo_id.split("/") if "/" in repo_id else (None, repo_id)

        path = f"{self.endpoint}/api/repos/create"

        if repo_type not in constants.REPO_TYPES:
            raise ValueError("Invalid repo type")

        json: Dict[str, Any] = {"name": name, "organization": organization}
        if private is not None:
            json["private"] = private
        if repo_type is not None:
            json["type"] = repo_type
        if repo_type == "space":
            if space_sdk is None:
                raise ValueError(
                    "No space_sdk provided. `create_repo` expects space_sdk to be one"
                    f" of {constants.SPACES_SDK_TYPES} when repo_type is 'space'`"
                )
            if space_sdk not in constants.SPACES_SDK_TYPES:
                raise ValueError(f"Invalid space_sdk. Please choose one of {constants.SPACES_SDK_TYPES}.")
            json["sdk"] = space_sdk

        if space_sdk is not None and repo_type != "space":
            warnings.warn("Ignoring provided space_sdk because repo_type is not 'space'.")

        function_args = [
            "space_hardware",
            "space_storage",
            "space_sleep_time",
            "space_secrets",
            "space_variables",
        ]
        json_keys = ["hardware", "storageTier", "sleepTimeSeconds", "secrets", "variables"]
        values = [space_hardware, space_storage, space_sleep_time, space_secrets, space_variables]

        if repo_type == "space":
            json.update({k: v for k, v in zip(json_keys, values) if v is not None})
        else:
            provided_space_args = [key for key, value in zip(function_args, values) if value is not None]

            if provided_space_args:
                warnings.warn(f"Ignoring provided {', '.join(provided_space_args)} because repo_type is not 'space'.")

        if getattr(self, "_lfsmultipartthresh", None):
            # Testing purposes only.
            # See https://github.com/huggingface/huggingface_hub/pull/733/files#r820604472
            json["lfsmultipartthresh"] = self._lfsmultipartthresh  # type: ignore

        if resource_group_id is not None:
            json["resourceGroupId"] = resource_group_id

        headers = self._build_hf_headers(token=token)
        while True:
            # r = get_session().post(path, headers=headers, json=json)
            r = {}
            if r.status_code == 409 and "Cannot create repo: another conflicting operation is in progress" in r.text:
                # Since https://github.com/huggingface/moon-landing/pull/7272 (private repo), it is not possible to
                # concurrently create repos on the Hub for a same user. This is rarely an issue, except when running
                # tests. To avoid any inconvenience, we retry to create the repo for this specific error.
                # NOTE: This could have being fixed directly in the tests but adding it here should fixed CIs for all
                # dependent libraries.
                # NOTE: If a fix is implemented server-side, we should be able to remove this retry mechanism.
                logger.debug("Create repo failed due to a concurrency issue. Retrying...")
                continue
            break

        try:
            # hf_raise_for_status(r)
            print('002')
        # except HTTPError as err:
        except Exception as err:
            if exist_ok and err.response.status_code == 409:
                # Repo already exists and `exist_ok=True`
                pass
            elif exist_ok and err.response.status_code == 403:
                # No write permission on the namespace but repo might already exist
                try:
                    self.repo_info(repo_id=repo_id, repo_type=repo_type, token=token)
                    if repo_type is None or repo_type == constants.REPO_TYPE_MODEL:
                        return RepoUrl(f"{self.endpoint}/{repo_id}")
                    return RepoUrl(f"{self.endpoint}/{repo_type}/{repo_id}")
                # except HfHubHTTPError:
                except Exception:
                    raise err
            else:
                raise

        d = r.json()
        return RepoUrl(d["url"], endpoint=self.endpoint)

    def preupload_lfs_files(
        self,
        repo_id: str,
        additions: Iterable[CommitOperationAdd],
        *,
        token: Union[str, bool, None] = None,
        repo_type: Optional[str] = None,
        revision: Optional[str] = None,
        create_pr: Optional[bool] = None,
        num_threads: int = 5,
        free_memory: bool = True,
        gitignore_content: Optional[str] = None,
    ):
        """Pre-upload LFS files to S3 in preparation on a future commit.

        This method is useful if you are generating the files to upload on-the-fly and you don't want to store them
        in memory before uploading them all at once.

        <Tip warning={true}>

        This is a power-user method. You shouldn't need to call it directly to make a normal commit.
        Use [`create_commit`] directly instead.

        </Tip>

        <Tip warning={true}>

        Commit operations will be mutated during the process. In particular, the attached `path_or_fileobj` will be
        removed after the upload to save memory (and replaced by an empty `bytes` object). Do not reuse the same
        objects except to pass them to [`create_commit`]. If you don't want to remove the attached content from the
        commit operation object, pass `free_memory=False`.

        </Tip>

        Args:
            repo_id (`str`):
                The repository in which you will commit the files, for example: `"username/custom_transformers"`.

            operations (`Iterable` of [`CommitOperationAdd`]):
                The list of files to upload. Warning: the objects in this list will be mutated to include information
                relative to the upload. Do not reuse the same objects for multiple commits.

            token (Union[bool, str, None], optional):
                A valid user access token (string). Defaults to the locally saved
                token, which is the recommended method for authentication (see
                https://huggingface.co/docs/huggingface_hub/quick-start#authentication).
                To disable authentication, pass `False`.

            repo_type (`str`, *optional*):
                The type of repository to upload to (e.g. `"model"` -default-, `"dataset"` or `"space"`).

            revision (`str`, *optional*):
                The git revision to commit from. Defaults to the head of the `"main"` branch.

            create_pr (`boolean`, *optional*):
                Whether or not you plan to create a Pull Request with that commit. Defaults to `False`.

            num_threads (`int`, *optional*):
                Number of concurrent threads for uploading files. Defaults to 5.
                Setting it to 2 means at most 2 files will be uploaded concurrently.

            gitignore_content (`str`, *optional*):
                The content of the `.gitignore` file to know which files should be ignored. The order of priority
                is to first check if `gitignore_content` is passed, then check if the `.gitignore` file is present
                in the list of files to commit and finally default to the `.gitignore` file already hosted on the Hub
                (if any).

        Example:
        ```py
        >>> from huggingface_hub import CommitOperationAdd, preupload_lfs_files, create_commit, create_repo

        >>> repo_id = create_repo("test_preupload").repo_id

        # Generate and preupload LFS files one by one
        >>> operations = [] # List of all `CommitOperationAdd` objects that will be generated
        >>> for i in range(5):
        ...     content = ... # generate binary content
        ...     addition = CommitOperationAdd(path_in_repo=f"shard_{i}_of_5.bin", path_or_fileobj=content)
        ...     preupload_lfs_files(repo_id, additions=[addition]) # upload + free memory
        ...     operations.append(addition)

        # Create commit
        >>> create_commit(repo_id, operations=operations, commit_message="Commit all shards")
        ```
        """
        repo_type = repo_type if repo_type is not None else constants.REPO_TYPE_MODEL
        if repo_type not in constants.REPO_TYPES:
            raise ValueError(f"Invalid repo type, must be one of {constants.REPO_TYPES}")
        revision = quote(revision, safe="") if revision is not None else constants.DEFAULT_REVISION
        create_pr = create_pr if create_pr is not None else False
        headers = self._build_hf_headers(token=token)

        # Check if a `gitignore` file is being committed to the Hub.
        additions = list(additions)
        if gitignore_content is None:
            for addition in additions:
                if addition.path_in_repo == ".gitignore":
                    with addition.as_file() as f:
                        gitignore_content = f.read().decode()
                        break

        # Filter out already uploaded files
        new_additions = [addition for addition in additions if not addition._is_uploaded]

        # Check which new files are LFS
        try:
            # _fetch_upload_modes(
            #     additions=new_additions,
            #     repo_type=repo_type,
            #     repo_id=repo_id,
            #     headers=headers,
            #     revision=revision,
            #     endpoint=self.endpoint,
            #     create_pr=create_pr or False,
            #     gitignore_content=gitignore_content,
            # )
            print('aaa')
        # except RepositoryNotFoundError as e:
        except Exception as e:
            # e.append_to_message(_CREATE_COMMIT_NO_REPO_ERROR_MESSAGE)
            raise

        # Filter out regular files
        new_lfs_additions = [addition for addition in new_additions if addition._upload_mode == "lfs"]

        # Filter out files listed in .gitignore
        new_lfs_additions_to_upload = []
        for addition in new_lfs_additions:
            if addition._should_ignore:
                logger.debug(f"Skipping upload for LFS file '{addition.path_in_repo}' (ignored by gitignore file).")
            else:
                new_lfs_additions_to_upload.append(addition)
        if len(new_lfs_additions) != len(new_lfs_additions_to_upload):
            logger.info(
                f"Skipped upload for {len(new_lfs_additions) - len(new_lfs_additions_to_upload)} LFS file(s) "
                "(ignored by gitignore file)."
            )

        # Upload new LFS files
        # _upload_lfs_files(
        #     additions=new_lfs_additions_to_upload,
        #     repo_type=repo_type,
        #     repo_id=repo_id,
        #     headers=headers,
        #     endpoint=self.endpoint,
        #     num_threads=num_threads,
        #     # If `create_pr`, we don't want to check user permission on the revision as users with read permission
        #     # should still be able to create PRs even if they don't have write permission on the target branch of the
        #     # PR (i.e. `revision`).
        #     revision=revision if not create_pr else None,
        # )
        for addition in new_lfs_additions_to_upload:
            addition._is_uploaded = True
            if free_memory:
                addition.path_or_fileobj = b""


    def create_commit(
        self,
        repo_id: str,
        operations: Iterable[CommitOperation],
        *,
        commit_message: str,
        commit_description: Optional[str] = None,
        token: Union[str, bool, None] = None,
        repo_type: Optional[str] = None,
        revision: Optional[str] = None,
        create_pr: Optional[bool] = None,
        num_threads: int = 5,
        parent_commit: Optional[str] = None,
        run_as_future: bool = False,
    ) -> Union[CommitInfo, Future[CommitInfo]]:
        """
        Creates a commit in the given repo, deleting & uploading files as needed.

        <Tip warning={true}>

        The input list of `CommitOperation` will be mutated during the commit process. Do not reuse the same objects
        for multiple commits.

        </Tip>

        <Tip warning={true}>

        `create_commit` assumes that the repo already exists on the Hub. If you get a
        Client error 404, please make sure you are authenticated and that `repo_id` and
        `repo_type` are set correctly. If repo does not exist, create it first using
        [`~hf_api.create_repo`].

        </Tip>

        <Tip warning={true}>

        `create_commit` is limited to 25k LFS files and a 1GB payload for regular files.

        </Tip>

        Args:
            repo_id (`str`):
                The repository in which the commit will be created, for example:
                `"username/custom_transformers"`

            operations (`Iterable` of [`~hf_api.CommitOperation`]):
                An iterable of operations to include in the commit, either:

                    - [`~hf_api.CommitOperationAdd`] to upload a file
                    - [`~hf_api.CommitOperationDelete`] to delete a file
                    - [`~hf_api.CommitOperationCopy`] to copy a file

                Operation objects will be mutated to include information relative to the upload. Do not reuse the
                same objects for multiple commits.

            commit_message (`str`):
                The summary (first line) of the commit that will be created.

            commit_description (`str`, *optional*):
                The description of the commit that will be created

            token (Union[bool, str, None], optional):
                A valid user access token (string). Defaults to the locally saved
                token, which is the recommended method for authentication (see
                https://huggingface.co/docs/huggingface_hub/quick-start#authentication).
                To disable authentication, pass `False`.

            repo_type (`str`, *optional*):
                Set to `"dataset"` or `"space"` if uploading to a dataset or
                space, `None` or `"model"` if uploading to a model. Default is
                `None`.

            revision (`str`, *optional*):
                The git revision to commit from. Defaults to the head of the `"main"` branch.

            create_pr (`boolean`, *optional*):
                Whether or not to create a Pull Request with that commit. Defaults to `False`.
                If `revision` is not set, PR is opened against the `"main"` branch. If
                `revision` is set and is a branch, PR is opened against this branch. If
                `revision` is set and is not a branch name (example: a commit oid), an
                `RevisionNotFoundError` is returned by the server.

            num_threads (`int`, *optional*):
                Number of concurrent threads for uploading files. Defaults to 5.
                Setting it to 2 means at most 2 files will be uploaded concurrently.

            parent_commit (`str`, *optional*):
                The OID / SHA of the parent commit, as a hexadecimal string.
                Shorthands (7 first characters) are also supported. If specified and `create_pr` is `False`,
                the commit will fail if `revision` does not point to `parent_commit`. If specified and `create_pr`
                is `True`, the pull request will be created from `parent_commit`. Specifying `parent_commit`
                ensures the repo has not changed before committing the changes, and can be especially useful
                if the repo is updated / committed to concurrently.
            run_as_future (`bool`, *optional*):
                Whether or not to run this method in the background. Background jobs are run sequentially without
                blocking the main thread. Passing `run_as_future=True` will return a [Future](https://docs.python.org/3/library/concurrent.futures.html#future-objects)
                object. Defaults to `False`.

        Returns:
            [`CommitInfo`] or `Future`:
                Instance of [`CommitInfo`] containing information about the newly created commit (commit hash, commit
                url, pr url, commit message,...). If `run_as_future=True` is passed, returns a Future object which will
                contain the result when executed.

        Raises:
            [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
                If commit message is empty.
            [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
                If parent commit is not a valid commit OID.
            [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
                If a README.md file with an invalid metadata section is committed. In this case, the commit will fail
                early, before trying to upload any file.
            [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
                If `create_pr` is `True` and revision is neither `None` nor `"main"`.
            [`~utils.RepositoryNotFoundError`]:
                If repository is not found (error 404): wrong repo_id/repo_type, private
                but not authenticated or repo does not exist.
        """
        if parent_commit is not None and not constants.REGEX_COMMIT_OID.fullmatch(parent_commit):
            raise ValueError(
                f"`parent_commit` is not a valid commit OID. It must match the following regex: {constants.REGEX_COMMIT_OID}"
            )

        if commit_message is None or len(commit_message) == 0:
            raise ValueError("`commit_message` can't be empty, please pass a value.")

        commit_description = commit_description if commit_description is not None else ""
        repo_type = repo_type if repo_type is not None else constants.REPO_TYPE_MODEL
        if repo_type not in constants.REPO_TYPES:
            raise ValueError(f"Invalid repo type, must be one of {constants.REPO_TYPES}")
        unquoted_revision = revision or constants.DEFAULT_REVISION
        revision = quote(unquoted_revision, safe="")
        create_pr = create_pr if create_pr is not None else False

        headers = self._build_hf_headers(token=token)

        operations = list(operations)
        additions = [op for op in operations if isinstance(op, CommitOperationAdd)]
        copies = [op for op in operations if isinstance(op, CommitOperationCopy)]
        nb_additions = len(additions)
        nb_copies = len(copies)
        nb_deletions = len(operations) - nb_additions - nb_copies

        for addition in additions:
            if addition._is_committed:
                raise ValueError(
                    f"CommitOperationAdd {addition} has already being committed and cannot be reused. Please create a"
                    " new CommitOperationAdd object if you want to create a new commit."
                )

        if repo_type != "dataset":
            for addition in additions:
                if addition.path_in_repo.endswith((".arrow", ".parquet")):
                    print(
                        f"It seems that you are about to commit a data file ({addition.path_in_repo}) to a {repo_type}"
                        " repository. You are sure this is intended? If you are trying to upload a dataset, please"
                        " set `repo_type='dataset'` or `--repo-type=dataset` in a CLI."
                    )

        # logger.debug(
        #     f"About to commit to the hub: {len(additions)} addition(s), {len(copies)} copie(s) and"
        #     f" {nb_deletions} deletion(s)."
        # )

        # If updating a README.md file, make sure the metadata format is valid
        # It's better to fail early than to fail after all the files have been uploaded.
        for addition in additions:
            if addition.path_in_repo == "README.md":
                with addition.as_file() as file:
                    content = file.read().decode()
                self._validate_yaml(content, repo_type=repo_type, token=token)
                # Skip other additions after `README.md` has been processed
                break

        # If updating twice the same file or update then delete a file in a single commit
        # _warn_on_overwriting_operations(operations)

        self.preupload_lfs_files(
            repo_id=repo_id,
            additions=additions,
            token=token,
            repo_type=repo_type,
            revision=unquoted_revision,  # first-class methods take unquoted revision
            create_pr=create_pr,
            num_threads=num_threads,
            free_memory=False,  # do not remove `CommitOperationAdd.path_or_fileobj` on LFS files for "normal" users
        )

        # Remove no-op operations (files that have not changed)
        operations_without_no_op = []
        for operation in operations:
            if (
                isinstance(operation, CommitOperationAdd)
                and operation._remote_oid is not None
                and operation._remote_oid == operation._local_oid
            ):
                # File already exists on the Hub and has not changed: we can skip it.
                logger.debug(f"Skipping upload for '{operation.path_in_repo}' as the file has not changed.")
                continue
            operations_without_no_op.append(operation)
        if len(operations) != len(operations_without_no_op):
            logger.info(
                f"Removing {len(operations) - len(operations_without_no_op)} file(s) from commit that have not changed."
            )

        # Return early if empty commit
        if len(operations_without_no_op) == 0:
            logger.warning("No files have been modified since last commit. Skipping to prevent empty commit.")

            # Get latest commit info
            try:
                info = self.repo_info(repo_id=repo_id, repo_type=repo_type, revision=unquoted_revision, token=token)
            # except RepositoryNotFoundError as e:
            except Exception as e:
                # e.append_to_message(_CREATE_COMMIT_NO_REPO_ERROR_MESSAGE)
                raise

            # Return commit info based on latest commit
            url_prefix = self.endpoint
            if repo_type is not None and repo_type != constants.REPO_TYPE_MODEL:
                url_prefix = f"{url_prefix}/{repo_type}s"
            return CommitInfo(
                commit_url=f"{url_prefix}/{repo_id}/commit/{info.sha}",
                commit_message=commit_message,
                commit_description=commit_description,
                oid=info.sha,  # type: ignore[arg-type]
            )

        # files_to_copy = _fetch_files_to_copy(
        #     copies=copies,
        #     repo_type=repo_type,
        #     repo_id=repo_id,
        #     headers=headers,
        #     revision=unquoted_revision,
        #     endpoint=self.endpoint,
        # )
        # commit_payload = _prepare_commit_payload(
        #     operations=operations,
        #     files_to_copy=files_to_copy,
        #     commit_message=commit_message,
        #     commit_description=commit_description,
        #     parent_commit=parent_commit,
        # )
        commit_payload = []
        commit_url = f"{self.endpoint}/api/{repo_type}s/{repo_id}/commit/{revision}"

        def _payload_as_ndjson() -> Iterable[bytes]:
            for item in commit_payload:
                yield json.dumps(item).encode()
                yield b"\n"

        headers = {
            # See https://github.com/huggingface/huggingface_hub/issues/1085#issuecomment-1265208073
            "Content-Type": "application/x-ndjson",
            **headers,
        }
        data = b"".join(_payload_as_ndjson())
        params = {"create_pr": "1"} if create_pr else None

        try:
            # commit_resp = get_session().post(url=commit_url, headers=headers, data=data, params=params)
            # hf_raise_for_status(commit_resp, endpoint_name="commit")
            commit_resp = {}
        # except RepositoryNotFoundError as e:
        except Exception as e:
            # e.append_to_message(_CREATE_COMMIT_NO_REPO_ERROR_MESSAGE)
            raise
        # except EntryNotFoundError as e:
        except Exception as e:
            if nb_deletions > 0 and "A file with this name doesn't exist" in str(e):
                e.append_to_message(
                    "\nMake sure to differentiate file and folder paths in delete"
                    " operations with a trailing '/' or using `is_folder=True/False`."
                )
            raise

        # Mark additions as committed (cannot be reused in another commit)
        for addition in additions:
            addition._is_committed = True

        commit_data = commit_resp.json()
        return CommitInfo(
            commit_url=commit_data["commitUrl"],
            commit_message=commit_message,
            commit_description=commit_description,
            oid=commit_data["commitOid"],
            pr_url=commit_data["pullRequestUrl"] if create_pr else None,
        )
