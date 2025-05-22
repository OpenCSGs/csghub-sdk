import typer
import os
from typing import Annotated, List, Optional
from pycsghub.cmd import repo, inference, finetune
from pycsghub.cmd.repo_types import RepoType
from importlib.metadata import version
from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN, DEFAULT_REVISION

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
    "repoID": typer.Argument(help="The ID of the repo. (e.g. `username/repo-name`)."),
    "localPath": typer.Argument(help="Local path to the file or folder to upload. Defaults to the relative path of the file of repo of OpenCSG Hub."),
    "pathInRepo": typer.Argument(help="Path of the folder in the repo. Defaults to the relative path of the file or folder."),
    "repoType": typer.Option("-t", "--repo-type", help="Specify the repository type."),
    "revision": typer.Option("-r", "--revision", help="An optional Git revision id which can be a branch name"),
    "cache_dir": typer.Option("-cd", "--cache-dir", help="Path to the directory where to save the downloaded files."),
    "endpoint": typer.Option("-e", "--endpoint", help="The address of the request to be sent."),
    "username": typer.Option("-u", "--username", help="Logon account of OpenCSG Hub."),
    "token": typer.Option("-k", "--token", help="A User Access Token generated from https://opencsg.com/settings/access-token"),
    "allow_patterns": typer.Option("--allow-patterns", help="Allow patterns for files to be downloaded."),
    "ignore_patterns": typer.Option("--ignore-patterns", help="Ignore patterns for files to be downloaded."),
    "version": typer.Option(None, "-V", "--version", callback=version_callback, is_eager=True, help="Show the version and exit."),
    "limit": typer.Option("--limit", help="Number of items to list"),
}

@app.command(name="download", help="Download model/dataset from OpenCSG Hub")
def download(
        repo_id: Annotated[str, OPTIONS["repoID"]],
        repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL, 
        revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
        cache_dir: Annotated[Optional[str], OPTIONS["cache_dir"]] = None,
        allow_patterns: Annotated[Optional[List[str]], OPTIONS["allow_patterns"]] = None,
        ignore_patterns: Annotated[Optional[List[str]], OPTIONS["ignore_patterns"]] = None,
    ):
    repo.download(
        repo_id=repo_id,
        repo_type=repo_type, 
        revision=revision, 
        cache_dir=cache_dir,
        endpoint=endpoint,
        token=token,
        allow_patterns=allow_patterns,
        ignore_patterns=ignore_patterns,
    )

@app.command(name="upload", help="Upload repository files to OpenCSG Hub")
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
    # File upload
    if os.path.isfile(local_path):
        repo.upload_files(
            repo_id=repo_id, 
            repo_type=repo_type, 
            repo_file=local_path,
            path_in_repo=path_in_repo,
            revision=revision, 
            endpoint=endpoint,
            token=token
        )
    # Folder upload
    else:
        repo.upload_folder(
            repo_id=repo_id, 
            repo_type=repo_type,
            local_path=local_path,
            path_in_repo=path_in_repo,
            revision=revision,
            endpoint=endpoint,
            token=token,
            user_name=user_name
        )

inference_app = typer.Typer(
    no_args_is_help=True,
    help="Manage inference instances on OpenCSG Hub"
)
app.add_typer(inference_app, name="inference")

@inference_app.command(name="list", help="List inference instances")
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

@inference_app.command(name="start", help="Start inference instance")
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


@inference_app.command(name="stop", help="Stop inference instance")
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

@finetune_app.command(name="list", help="List fine-tuning instances")
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

@finetune_app.command(name="start", help="Start fine-tuning instance")
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

@finetune_app.command(name="stop", help="Stop fine-tuning instance")
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
def main(version: bool = OPTIONS["version"]):
    pass


if __name__ == "__main__":
    app()
