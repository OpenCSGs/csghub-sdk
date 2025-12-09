import logging
import os
import time
import warnings
from importlib.metadata import version
from typing import List, Optional

import dotenv
import typer
try:
    from huggingface_hub.file_download import DryRunFileInfo
except ImportError:
    from collections import namedtuple
    DryRunFileInfo = namedtuple('DryRunFileInfo', ['path', 'size', 'hash'])

dotenv.load_dotenv()
from huggingface_hub.utils import disable_progress_bars, enable_progress_bars
from typing_extensions import Annotated

from pycsghub.cmd import finetune, inference, system
from pycsghub.cmd.repo_types import RepoType
from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN, DEFAULT_REVISION, REPO_SOURCE_CSG
from pycsghub.api_client import get_csghub_api
from .utils import print_download_result
from .lfs import LfsEnableCommand, LfsUploadCommand
from .upload_large_folder.main import upload_large_folder_internal

logger = logging.getLogger(__name__)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
)

def version_callback(value: bool):
    if value:
        pkg_version = version("csghub-sdk")
        print(f"csghub-cli version {pkg_version}")
        raise typer.Exit()

OPTIONS = {
    "repoID"            : typer.Argument(help="The ID of the repo. (e.g. `username/repo-name`)."),
    "localPath"         : typer.Argument(
        help="Local path to the file to upload. Defaults to the relative path of the file of repo of OpenCSG Hub."),
    "pathInRepo"        : typer.Argument(
        help="Path of the folder in the repo. Defaults to the relative path of the file or folder."),
    "repoType"          : typer.Option("-t", "--repo-type", help="Specify the repository type."),
    "revision"          : typer.Option("-r", "--revision",
                                       help="An optional Git revision id which can be a branch name"),
    "cache_dir"         : typer.Option("-cd", "--cache-dir",
                                       help="Path to the directory where to save the downloaded files."),
    "local_dir"         : typer.Option("-ld", "--local-dir",
                                       help="If provided, the downloaded files will be placed under this directory."),
    "endpoint"          : typer.Option("-e", "--endpoint", help="The address of the request to be sent."),
    "username"          : typer.Option("-u", "--username", help="Logon account of OpenCSG Hub."),
    "token"             : typer.Option("-k", "--token",
                                       help="A User Access Token generated from https://opencsg.com/settings/access-token"),
    "allow_patterns"    : typer.Option("--allow-patterns", help="Allow patterns for files to be downloaded."),
    "ignore_patterns"   : typer.Option("--ignore-patterns", help="Ignore patterns for files to be downloaded."),
    "quiet"             : typer.Option("--quiet",
                                       help="Disable progress bars and warnings; print only essential results."),
    "dry_run"           : typer.Option("--dry-run",
                                       help="Show what would be downloaded or uploaded without performing actions."),
    "force_download"    : typer.Option("--force-download", help="Download even if files are already cached."),
    "max_workers"       : typer.Option("-mw", "--max-workers", help="Maximum workers used for downloading."),
    "version"           : typer.Option(None, "-V", "--version", callback=version_callback, is_eager=True,
                                       help="Show the version and exit."),
    "limit"             : typer.Option("--limit", help="Number of items to list"),
    "localFolder"       : typer.Argument(help="Local path to the folder to upload."),
    "num_workers"       : typer.Option("-n", "--num-workers", help="Number of concurrent upload workers."),
    "print_report"      : typer.Option("--print-report",
                                       help="Whether to print a report of the upload progress. Defaults to True."),
    "print_report_every": typer.Option("--print-report-every",
                                       help="Frequency at which the report is printed. Defaults to 60 seconds."),
    "include"           : typer.Option("--include", help="Glob patterns to match files to upload."),
    "exclude"           : typer.Option("--exclude", help="Glob patterns to exclude from files to upload."),
    "delete"            : typer.Option("--delete", help="Glob patterns for files to delete while committing."),
    "commit_message"    : typer.Option("--commit-message", help="Commit message for uploads."),
    "commit_description": typer.Option("--commit-description", help="Commit description for uploads."),
    "create_pr"         : typer.Option("--create-pr", help="Upload content as a new Pull Request."),
    "private"           : typer.Option("--private", help="Create private repo if auto-created."),
    "every"             : typer.Option("--every", help="Schedule background commits every N minutes."),
    "log_level"         : typer.Option("INFO", "-L", "--log-level",
                                       help="set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
                                       case_sensitive=False,
                                       ),
    "source"            : typer.Option("--source",
                                       help="Specify the source of the repository (e.g. 'csg', 'hf', 'ms')."),
    "path"              : typer.Argument(help="Local path to repository you want to configure."),
}

@app.command(name="download", help="Download model/dataset/space from OpenCSG Hub", no_args_is_help=True)
def download(
    repo_id: Annotated[str, OPTIONS["repoID"]],
    filenames: Annotated[
        Optional[List[str]],
        typer.Argument(
            help="Files to download (e.g. `config.json`, `data/metadata.jsonl`).",
        ),
    ] = None,
    repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL,
    revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
    token: Annotated[Optional[str], OPTIONS["token"]] = None,
    cache_dir: Annotated[Optional[str], OPTIONS["cache_dir"]] = None,
    local_dir: Annotated[Optional[str], OPTIONS["local_dir"]] = None,
    allow_patterns: Annotated[Optional[List[str]], OPTIONS["allow_patterns"]] = None,
    ignore_patterns: Annotated[Optional[List[str]], OPTIONS["ignore_patterns"]] = None,
    source: Annotated[str, OPTIONS["source"]] = REPO_SOURCE_CSG,
    quiet: Annotated[Optional[bool], OPTIONS["quiet"]] = False,
    dry_run: Annotated[Optional[bool], OPTIONS["dry_run"]] = False,
    force_download: Annotated[Optional[bool], OPTIONS["force_download"]] = False,
    max_workers: Annotated[Optional[int], OPTIONS["max_workers"]] = 8,
):
    api = get_csghub_api(token=token, endpoint=endpoint)
    
    # Handle single/multiple file args similar to HF
    filenames_list = filenames if filenames is not None else []
    
    # If filenames are provided, use them as allow_patterns or download single file
    if len(filenames_list) > 0:
        if allow_patterns is not None and len(allow_patterns) > 0:
            warnings.warn("Ignoring --allow-patterns since filenames have been explicitly set.")
        if ignore_patterns is not None and len(ignore_patterns) > 0:
            warnings.warn("Ignoring --ignore-patterns since filenames have been explicitly set.")
        
        # Single file case: use hf_hub_download (or equivalent)
        if len(filenames_list) == 1:
            download_kwargs = {
                "repo_id"       : repo_id,
                "repo_type"     : repo_type.value,
                "revision"      : revision,
                "filename"      : filenames_list[0],
                "cache_dir"     : cache_dir,
                "force_download": force_download,
                "token"         : token,
                "local_dir"     : local_dir,
            }
            
            # Explicitly pass endpoint for CsgXnetApi if available
            # Note: HfApi.hf_hub_download might not accept 'endpoint' as a keyword argument in some versions.
            # But we can try to pass it if it's CsghubApi (our wrapper) OR relying on instance state.
            # However, if we are calling api.hf_hub_download (HfApi method), it usually uses self.endpoint.
            # If we pass 'endpoint', it might fail if the method signature doesn't accept it.
            # Let's rely on api instance having the correct endpoint set (which we fixed in CsgXnetApi.__init__).
            # if hasattr(api, 'endpoint') and api.endpoint:
            #     download_kwargs["endpoint"] = api.endpoint
            
            # Only pass extra args if API supports them (CsghubApi)
            if api.__class__.__name__ == "CsghubApi":
                download_kwargs["quiet"] = quiet
                download_kwargs["source"] = source
                download_kwargs["dry_run"] = dry_run
            
            try:
                result = api.hf_hub_download(**download_kwargs)
                print_download_result(result)
            except Exception as e:
                if quiet:
                    raise e
                print(f"Download failed: {e}")
                raise typer.Exit(code=1)
            return
        
        # Multiple files case: use snapshot_download with allow_patterns
        allow_patterns = filenames_list
        ignore_patterns = None
    
    snapshot_kwargs = {
        "repo_id"        : repo_id,
        "repo_type"      : repo_type.value,
        "revision"       : revision,
        "cache_dir"      : cache_dir,
        "local_dir"      : local_dir,
        "allow_patterns" : allow_patterns,
        "ignore_patterns": ignore_patterns,
        "force_download" : force_download,
        "max_workers"    : max_workers,
    }
    if api.__class__.__name__ == "CsghubApi":
        snapshot_kwargs["source"] = source
        snapshot_kwargs["quiet"] = quiet
    
    try:
        result = api.snapshot_download(**snapshot_kwargs)
    except Exception as e:
        if quiet:
            raise e
        print(f"Download failed: {e}")
        raise typer.Exit(code=1)
    
    if quiet:
        disable_progress_bars()
        print_download_result(result)
        enable_progress_bars()
    else:
        print_download_result(result)

@app.command(name="upload", help="Upload repository files to OpenCSG Hub", no_args_is_help=True)
def upload(
    repo_id: Annotated[str, OPTIONS["repoID"]],
    local_path: Annotated[str, OPTIONS["localPath"]],
    path_in_repo: Annotated[str, OPTIONS["pathInRepo"]] = "",
    repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL,
    revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
    token: Annotated[Optional[str], OPTIONS["token"]] = None,
    user_name: Annotated[Optional[str], OPTIONS["username"]] = "",
    include: Annotated[Optional[List[str]], OPTIONS["include"]] = None,
    exclude: Annotated[Optional[List[str]], OPTIONS["exclude"]] = None,
    delete: Annotated[Optional[List[str]], OPTIONS["delete"]] = None,
    commit_message: Annotated[Optional[str], OPTIONS["commit_message"]] = None,
    commit_description: Annotated[Optional[str], OPTIONS["commit_description"]] = None,
    create_pr: Annotated[Optional[bool], OPTIONS["create_pr"]] = False,
    private: Annotated[Optional[bool], OPTIONS["private"]] = False,
    every: Annotated[Optional[float], OPTIONS["every"]] = None,
    quiet: Annotated[bool, OPTIONS["quiet"]] = False,
):
    repo_type_str = repo_type.value
    api = get_csghub_api(token=token, endpoint=endpoint, user_name=user_name)
    
    resolved_local_path = local_path
    resolved_path_in_repo = path_in_repo
    resolved_include = include
    
    def run_upload() -> dict:
        if os.path.isfile(resolved_local_path):
            if resolved_include is not None and len(resolved_include) > 0:
                warnings.warn("Ignoring --include since a single file is uploaded.")
            if exclude is not None and len(exclude) > 0:
                warnings.warn("Ignoring --exclude since a single file is uploaded.")
            if delete is not None and len(delete) > 0:
                warnings.warn("Ignoring --delete since a single file is uploaded.")
        
        if every is not None:
            # Placeholder for Scheduler
            # Scheduler not implemented yet in csghub-sdk
            # Similar to HF CommitScheduler logic
            print(f"Scheduling commits every {every} minutes... (Not fully implemented)")
            try:
                while True:
                    time.sleep(100)
            except KeyboardInterrupt:
                return "Stopped scheduled commits."
        
        if not os.path.isfile(resolved_local_path) and not os.path.isdir(resolved_local_path):
            raise FileNotFoundError(f"No such file or directory: '{resolved_local_path}'.")
        
        # Create repo if needed
        api.create_repo(
            repo_id=repo_id,
            repo_type=repo_type_str,
            exist_ok=True,
            private=private
        )
        
        # Check/Create branch
        if revision is not None and not create_pr:
            try:
                api.repo_info(repo_id=repo_id, repo_type=repo_type_str, revision=revision)
            except Exception:  # RevisionNotFoundError
                logger.info(f"Branch '{revision}' not found. Creating it...")
                api.create_branch(repo_id=repo_id, repo_type=repo_type_str, branch=revision, exist_ok=True)
        
        if os.path.isfile(resolved_local_path):
            return api.upload_file(
                path_or_fileobj=resolved_local_path,
                path_in_repo=resolved_path_in_repo or os.path.basename(resolved_local_path),
                repo_id=repo_id,
                repo_type=repo_type_str,
                revision=revision,
                commit_message=commit_message,
                commit_description=commit_description,
                create_pr=create_pr,
            )
        
        return api.upload_folder(
            folder_path=resolved_local_path,
            path_in_repo=resolved_path_in_repo,
            repo_id=repo_id,
            repo_type=repo_type_str,
            revision=revision,
            commit_message=commit_message,
            commit_description=commit_description,
            create_pr=create_pr,
            allow_patterns=resolved_include,
            ignore_patterns=exclude,
            delete_patterns=delete,
        )
    
    if quiet:
        disable_progress_bars()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            print(run_upload())
        enable_progress_bars()
    else:
        print(run_upload())

@app.command(name="upload-large-folder", help="Upload large folder to OpenCSG Hub using multiple workers",
             no_args_is_help=True)
def upload_large_folder(
    repo_id: Annotated[str, OPTIONS["repoID"]],
    local_path: Annotated[str, OPTIONS["localFolder"]],
    repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL,
    revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
    token: Annotated[Optional[str], OPTIONS["token"]] = None,
    allow_patterns: Annotated[Optional[List[str]], OPTIONS["allow_patterns"]] = None,
    ignore_patterns: Annotated[Optional[List[str]], OPTIONS["ignore_patterns"]] = None,
    num_workers: Annotated[int, OPTIONS["num_workers"]] = None,
    print_report: Annotated[bool, OPTIONS["print_report"]] = False,
    print_report_every: Annotated[int, OPTIONS["print_report_every"]] = 60,
):
    upload_large_folder_internal(
        repo_id=repo_id,
        local_path=local_path,
        repo_type=repo_type.value,
        revision=revision,
        endpoint=endpoint,
        token=token,
        allow_patterns=allow_patterns,
        ignore_patterns=ignore_patterns,
        num_workers=num_workers,
        print_report=print_report,
        print_report_every=print_report_every,
    )

@app.command(name="lfs-enable-largefiles", help="Configure your repository to enable upload of files > 5GB.",
             no_args_is_help=True)
def lfs_enable_largefiles(path: Annotated[str, OPTIONS["path"]]):
    lfsCmd = LfsEnableCommand(path)
    lfsCmd.run()

@app.command(name="lfs-multipart-upload", hidden=True)
def lfs_multipart_upload():
    lfsCmd = LfsUploadCommand()
    lfsCmd.run()

@app.command(name="env", help="Print information about the environment.")
def env():
    system.env()

@app.command(name="version", help="Print information about the hf version.")
def version():
    system.version()

inference_app = typer.Typer(
    no_args_is_help=True,
    help="Manage inference instances on OpenCSG Hub"
)
app.add_typer(inference_app, name="inference")

@inference_app.command(name="list", help="List inference instances", no_args_is_help=True)
def list_inferences(
    user_name: Annotated[str, OPTIONS["username"]],
    token: Annotated[str, OPTIONS["token"]] = None,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
    limit: Annotated[Optional[int], OPTIONS["limit"]] = 50,
):
    inference.list(
        user_name=user_name,
        token=token,
        endpoint=endpoint,
        limit=limit,
    )

@inference_app.command(name="start", help="Start inference instance", no_args_is_help=True)
def start_inference(
    model: str = typer.Argument(..., help="model to use for inference"),
    id: int = typer.Argument(..., help="ID of the inference instance to start"),
    token: Annotated[Optional[str], OPTIONS["token"]] = None,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
):
    inference.start(
        id=id,
        model=model,
        token=token,
        endpoint=endpoint,
    )

@inference_app.command(name="stop", help="Stop inference instance", no_args_is_help=True)
def stop_inference(
    model: str = typer.Argument(..., help="model to use for inference"),
    id: int = typer.Argument(..., help="ID of the inference instance to start"),
    token: Annotated[Optional[str], OPTIONS["token"]] = None,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
):
    inference.stop(
        id=id,
        model=model,
        token=token,
        endpoint=endpoint,
    )

finetune_app = typer.Typer(
    no_args_is_help=True,
    help="Manage fine-tuning instances on OpenCSG Hub"
)
app.add_typer(finetune_app, name="finetune")

@finetune_app.command(name="list", help="List fine-tuning instances", no_args_is_help=True)
def list_finetune(
    user_name: Annotated[str, OPTIONS["username"]],
    token: Annotated[str, OPTIONS["token"]] = None,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
    limit: Annotated[Optional[int], OPTIONS["limit"]] = 50,
):
    finetune.list(
        user_name=user_name,
        token=token,
        endpoint=endpoint,
        limit=limit,
    )

@finetune_app.command(name="start", help="Start fine-tuning instance", no_args_is_help=True)
def start_finetune(
    model: str = typer.Argument(..., help="model to use for fine-tuning"),
    id: int = typer.Argument(..., help="ID of the fine-tuning instance to start"),
    token: Annotated[Optional[str], OPTIONS["token"]] = None,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
):
    finetune.start(
        id=id,
        model=model,
        token=token,
        endpoint=endpoint,
    )

@finetune_app.command(name="stop", help="Stop fine-tuning instance", no_args_is_help=True)
def stop_finetune(
    model: str = typer.Argument(..., help="model to use for fine-tuning"),
    id: int = typer.Argument(..., help="ID of the fine-tuning instance to stop"),
    token: Annotated[Optional[str], OPTIONS["token"]] = None,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
):
    finetune.stop(
        id=id,
        model=model,
        token=token,
        endpoint=endpoint,
    )

@app.callback(
    invoke_without_command=True,
    no_args_is_help=True,
    help="OpenCSG Hub CLI",
    context_settings={
        "help_option_names": ["-h", "--help"],
    }
)
def main(
    version: Optional[bool] = OPTIONS["version"],
    log_level: str = OPTIONS["log_level"]
):
    # for example: format='%(asctime)s - %(name)s:%(funcName)s:%(lineno)d - %(levelname)s - %(message)s',
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler()]
    )
    pass

if __name__ == "__main__":
    app()
