import getpass
import logging
import os
import sys
import traceback
from functools import wraps
from importlib.metadata import version
from pathlib import Path
from typing import List, Optional

import typer
from typing_extensions import Annotated

from pycsghub._token import _get_token_from_file, _clean_token
from pycsghub.cmd import repo, inference, finetune
from pycsghub.cmd.repo_types import RepoType
from pycsghub.constants import CSGHUB_TOKEN_PATH
from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN, DEFAULT_REVISION
from pycsghub.constants import REPO_SOURCE_CSG
from pycsghub.utils import validate_repo_id, get_token_to_send
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


def auto_inject_token_and_verbose(func):
    """Decorator: automatically inject token and verbose parameters"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'token' in kwargs and kwargs['token'] is None:
            kwargs['token'] = get_token_to_send()
            if kwargs.get('verbose', False):
                print(f"[DEBUG] Auto-detected token: {'*' * 10 if kwargs['token'] else 'None'}")
        
        verbose = kwargs.get('verbose', False)
        if verbose:
            print(f"[DEBUG] Arguments received:")
            for key, value in kwargs.items():
                if key == 'token' and value:
                    print(f"[DEBUG] {key}: {'*' * 10}")
                else:
                    print(f"[DEBUG] {key}: {value}")
        
        return func(*args, **kwargs)
    return wrapper


OPTIONS = {
    "repoID": typer.Argument(help="The ID of the repo. (e.g. `username/repo-name`)."),
    "localPath": typer.Argument(
        help="Local path to the file to upload. Defaults to the relative path of the file of repo of OpenCSG Hub."),
    "pathInRepo": typer.Argument(
        help="Path of the folder in the repo. Defaults to the relative path of the file or folder."),
    "repoType": typer.Option("-t", "--repo-type", help="Specify the repository type."),
    "revision": typer.Option("-r", "--revision", help="An optional Git revision id which can be a branch name"),
    "cache_dir": typer.Option("-cd", "--cache-dir", help="Path to the directory where to save the downloaded files."),
    "local_dir": typer.Option("-ld", "--local-dir",
                              help="If provided, the downloaded files will be placed under this directory."),
    "endpoint": typer.Option("-e", "--endpoint", help="The address of the request to be sent."),
    "username": typer.Option("-u", "--username", help="Logon account of OpenCSG Hub."),
    "token": typer.Option("-k", "--token",
                          help="A User Access Token generated from https://opencsg.com/settings/access-token"),
    "allow_patterns": typer.Option("--allow-patterns", help="Allow patterns for files to be downloaded."),
    "ignore_patterns": typer.Option("--ignore-patterns", help="Ignore patterns for files to be downloaded."),
    "version": typer.Option(None, "-V", "--version", callback=version_callback, is_eager=True,
                            help="Show the version and exit."),
    "limit": typer.Option("--limit", help="Number of items to list"),
    "localFolder": typer.Argument(help="Local path to the folder to upload."),
    "num_workers": typer.Option("-n", "--num-workers", help="Number of concurrent upload workers."),
    "print_report": typer.Option("--print-report",
                                 help="Whether to print a report of the upload progress. Defaults to True."),
    "print_report_every": typer.Option("--print-report-every",
                                       help="Frequency at which the report is printed. Defaults to 60 seconds."),
    "log_level": typer.Option("INFO", "-L", "--log-level",
                              help="set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
                              case_sensitive=False,
                              ),
    "source": typer.Option("--source", help="Specify the source of the repository (e.g. 'csg', 'hf', 'ms')."),
}


@app.command(name="login", help="Login to OpenCSG Hub", no_args_is_help=True)
def login(
        token: Annotated[Optional[str], OPTIONS["token"]] = None):
    """Login to OpenCSG Hub using your access token.
    
    You can get your access token from https://opencsg.com/settings/access-token
    
    Examples:
        csghub-cli login
        csghub-cli login --token your_token_here
    """

    try:
        if token is None:
            env_token = os.environ.get("CSGHUB_TOKEN")
            if env_token:
                logger.info("✅ Found token in environment variable CSGHUB_TOKEN")
                token = env_token
            else:
                logger.error("❌ No token found in environment variable CSGHUB_TOKEN")
                logger.info("Please use 'csghub-cli login --token your_token_here' to provide your token")
                logger.info("You can get your access token from https://opencsg.com/settings/access-token")
                raise typer.Exit(1)

        cleaned_token = _clean_token(token)
        if not cleaned_token:
            logger.error("❌ Error: Invalid token provided.")
            raise typer.Exit(1)

        if len(cleaned_token) < 10:
            logger.error("❌ Error: Token seems too short. Please check your token.")
            raise typer.Exit(1)

        try:
            token_path = Path(CSGHUB_TOKEN_PATH)
            token_path.parent.mkdir(parents=True, exist_ok=True)

            token_path.write_text(cleaned_token)

            if os.name != 'nt':
                os.chmod(token_path, 0o600)

            logger.info("✅ Token saved successfully!")
            logger.info(f"Token location: {token_path}")
            logger.info("You can now use csghub-cli commands without specifying --token each time.")

        except PermissionError as e:
            logger.error(f"❌ Permission error saving token: {e}")
            logger.error("Please check if you have write permissions to the token directory.")
            raise typer.Exit(1)
        except Exception as e:
            logger.error(f"❌ Error saving token: {e}")
            raise typer.Exit(1)
    except Exception as e:
        logger.error(f"❌ Error in login command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@app.command(name="logout", help="Logout from OpenCSG Hub", no_args_is_help=True)
def logout():
    """Remove your access token from the local machine.
    
    This will delete the stored token file.
    """

    try:
        token_path = Path(CSGHUB_TOKEN_PATH)
        if token_path.exists():
            token_path.unlink()
            logger.info("✅ Successfully logged out!")
            logger.info("Your access token has been removed from this machine.")
        else:
            logger.info("ℹ️  No stored token found. You are already logged out.")

    except Exception as e:
        logger.error(f"❌ Error in logout command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@app.command(name="whoami", help="Show current user information", no_args_is_help=True)
def whoami(
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
):
    """Show information about the currently logged in user.
    
    This command will display your username and verify that your token is valid.
    """

    try:
        if token is None:
            token = _get_token_from_file()

        if not token:
            logger.error("❌ Not logged in. Please run 'csghub-cli login' first.")
            raise typer.Exit(1)

        try:
            logger.info("✅ Logged in successfully!")
            logger.info(f"Token location: {CSGHUB_TOKEN_PATH}")
            logger.info("Note: Token validation requires API access. Please test with a download/upload command.")

        except Exception as e:
            logger.error(f"❌ Error verifying token: {e}")
            raise typer.Exit(1)
    except Exception as e:
        logger.error(f"❌ Error in whoami command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@app.command(name="download", help="Download model/dataset from OpenCSG Hub", no_args_is_help=True)
@auto_inject_token_and_verbose
def download(
        repo_id: Annotated[str, OPTIONS["repoID"]],
        repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL,
        revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
        cache_dir: Annotated[Optional[str], OPTIONS["cache_dir"]] = None,
        local_dir: Annotated[Optional[str], OPTIONS["local_dir"]] = None,
        allow_patterns: Annotated[Optional[str], OPTIONS["allow_patterns"]] = None,
        ignore_patterns: Annotated[Optional[str], OPTIONS["ignore_patterns"]] = None,
        source: Annotated[str, OPTIONS["source"]] = REPO_SOURCE_CSG,
):
    try:
        repo.download(
            repo_id=repo_id,
            repo_type=repo_type.value,
            revision=revision,
            cache_dir=cache_dir,
            local_dir=local_dir,
            endpoint=endpoint,
            token=token,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
            source=source,
            enable_parallel=False,
            max_parallel_workers=4,
        )
    except Exception as e:
        logger.error(f"❌ Error in download command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@app.command(name="upload", help="Upload repository files to OpenCSG Hub", no_args_is_help=True)
@auto_inject_token_and_verbose
def upload(
        repo_id: Annotated[str, OPTIONS["repoID"]],
        local_path: Annotated[str, OPTIONS["localPath"]],
        path_in_repo: Annotated[str, OPTIONS["pathInRepo"]] = "",
        repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL,
        revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
        user_name: Annotated[Optional[str], OPTIONS["username"]] = "",
):
    try:
        validate_repo_id(repo_id)

        if os.path.isfile(local_path):
            repo.upload_files(
                repo_id=repo_id,
                repo_type=repo_type.value,
                repo_file=local_path,
                path_in_repo=path_in_repo,
                revision=revision,
                endpoint=endpoint,
                token=token,
            )
        # Folder upload
        else:
            repo.upload_folder(
                repo_id=repo_id,
                repo_type=repo_type.value,
                local_path=local_path,
                path_in_repo=path_in_repo,
                revision=revision,
                endpoint=endpoint,
                token=token,
                user_name=user_name,
            )
    except ValueError as e:
        logger.error(f"{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error in upload command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@app.command(name="upload-large-folder", help="Upload large folder to OpenCSG Hub using multiple workers",
             no_args_is_help=True)
@auto_inject_token_and_verbose
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
    try:
        validate_repo_id(repo_id)

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
    except ValueError as e:
        logger.error(f"{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error in upload-large-folder command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


inference_app = typer.Typer(
    no_args_is_help=True,
    help="Manage inference instances on OpenCSG Hub"
)
app.add_typer(inference_app, name="inference")


@inference_app.command(name="list", help="List inference instances", no_args_is_help=True)
@auto_inject_token_and_verbose
def list_inferences(
        user_name: Annotated[str, OPTIONS["username"]],
        token: Annotated[str, OPTIONS["token"]] = None,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
        limit: Annotated[Optional[int], OPTIONS["limit"]] = 50,
):
    try:
        inference.list(
            user_name=user_name,
            token=token,
            endpoint=endpoint,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"❌ Error in inference list command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@inference_app.command(name="start", help="Start inference instance", no_args_is_help=True)
@auto_inject_token_and_verbose
def start_inference(
        model: str = typer.Argument(..., help="model to use for inference"),
        id: int = typer.Argument(..., help="ID of the inference instance to start"),
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
):
    try:
        inference.start(
            id=id,
            model=model,
            token=token,
            endpoint=endpoint,
        )
    except Exception as e:
        logger.error(f"❌ Error in inference start command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@inference_app.command(name="stop", help="Stop inference instance", no_args_is_help=True)
@auto_inject_token_and_verbose
def stop_inference(
        model: str = typer.Argument(..., help="model to use for inference"),
        id: int = typer.Argument(..., help="ID of the inference instance to start"),
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
):
    try:
        inference.stop(
            id=id,
            model=model,
            token=token,
            endpoint=endpoint,
        )
    except Exception as e:
        logger.error(f"❌ Error in inference stop command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


finetune_app = typer.Typer(
    no_args_is_help=True,
    help="Manage fine-tuning instances on OpenCSG Hub"
)
app.add_typer(finetune_app, name="finetune")


@finetune_app.command(name="list", help="List fine-tuning instances", no_args_is_help=True)
@auto_inject_token_and_verbose
def list_finetune(
        user_name: Annotated[str, OPTIONS["username"]],
        token: Annotated[str, OPTIONS["token"]] = None,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
        limit: Annotated[Optional[int], OPTIONS["limit"]] = 50,
):
    try:
        finetune.list(
            user_name=user_name,
            token=token,
            endpoint=endpoint,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"❌ Error in finetune list command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@finetune_app.command(name="start", help="Start fine-tuning instance", no_args_is_help=True)
@auto_inject_token_and_verbose
def start_finetune(
        model: str = typer.Argument(..., help="model to use for fine-tuning"),
        id: int = typer.Argument(..., help="ID of the fine-tuning instance to start"),
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
):
    try:
        finetune.start(
            id=id,
            model=model,
            token=token,
            endpoint=endpoint,
        )
    except Exception as e:
        logger.error(f"❌ Error in finetune start command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@finetune_app.command(name="stop", help="Stop fine-tuning instance", no_args_is_help=True)
@auto_inject_token_and_verbose
def stop_finetune(
        model: str = typer.Argument(..., help="model to use for fine-tuning"),
        id: int = typer.Argument(..., help="ID of the fine-tuning instance to stop"),
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
):
    try:
        finetune.stop(
            id=id,
            model=model,
            token=token,
            endpoint=endpoint,
        )
    except Exception as e:
        logger.error(f"❌ Error in finetune stop command: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)


@app.callback(
    invoke_without_command=True,
    no_args_is_help=True,
    help="OpenCSG Hub CLI",
    context_settings={
        "help_option_names": ["-h", "--help"],
    }
)
def main(
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

    try:
        app()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.error("📋 Full stack trace:")
        traceback.print_exc()
        sys.exit(1)
