import typer
from typing import Annotated, List, Optional
from pycsghub.cmd import repo
from pycsghub.cmd.repo_types import RepoType
from importlib.metadata import version
from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN, DEFAULT_REVISION, MIRROR

app = typer.Typer(add_completion=False)

def version_callback(value: bool):
    if value:
        pkg_version = version("csghub-sdk")
        print(f"csghub-cli version {pkg_version}")
        raise typer.Exit()

OPTIONS = {
    "repoID": typer.Argument(help="The ID of the repo. (e.g. `username/repo-name`)."),
    "repoFiles": typer.Argument(help="Local path to the file or files to upload. Defaults to the relative path of the file of repo of OpenCSG Hub."),
    "repoType": typer.Option("-t", "--repo-type", help="Specify the repository type."),
    "revision": typer.Option("-r", "--revision", help="An optional Git revision id which can be a branch name"),
    "cache_dir": typer.Option("-cd", "--cache-dir", help="Path to the directory where to save the downloaded files."),
    "endpoint": typer.Option("-e", "--endpoint", help="The address of the request to be sent."),
    "token": typer.Option("-k", "--token", help="A User Access Token generated from https://opencsg.com/settings/access-token"),
    "mirror": typer.Option("-m", "--mirror", help="the mirror of the csghub repo to download, available value: auto, hf, csghub, default: csghub. hf: can download model/dataset with huggingface repo id. csghub: can download model/dataset with csghub repo id. auto: both repo id can download model/dataset"),
    "version": typer.Option(None, "-V", "--version", callback=version_callback, is_eager=True, help="Show the version and exit."),
}


@app.command(name="download", help="Download model/dataset from opencsg.com")
def download(
    repo_id: Annotated[str, OPTIONS["repoID"]],
    repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL,
    revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
    token: Annotated[Optional[str], OPTIONS["token"]] = None,
    cache_dir: Annotated[Optional[str], OPTIONS["cache_dir"]] = None,
    mirror: Annotated[Optional[str], OPTIONS["mirror"]] = MIRROR.AUTO,
):
    repo.download(
        repo_id=repo_id,
        repo_type=repo_type,
        revision=revision,
        cache_dir=cache_dir,
        endpoint=endpoint,
        token=token
    )


@app.command(name="upload", help="Upload repository files to opencsg.com.")
def upload(
    repo_id: Annotated[str, OPTIONS["repoID"]],
    repo_files: Annotated[List[str], OPTIONS["repoFiles"]],
    repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL,
    revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
    endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
    token: Annotated[Optional[str], OPTIONS["token"]] = None,
):
    repo.upload(
        repo_id=repo_id,
        repo_type=repo_type,
        repo_files=repo_files,
        revision=revision,
        endpoint=endpoint,
        token=token
    )
 
@app.callback(invoke_without_command=True)
def main(version: bool = OPTIONS["version"]):
    pass


if __name__ == "__main__":
    app()
