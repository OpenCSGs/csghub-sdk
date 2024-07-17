import typer
from typing import Annotated, List, Optional
from pycsghub.cmd import repo
from pycsghub.cmd.repo_types import RepoType
from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN, DEFAULT_REVISION

app = typer.Typer(add_completion=False)

OPTIONS = {
    "repoType": typer.Option(default=..., help="Specify the repository type."),
    "repoID": typer.Option(default=..., help="Specify the repository ID."),
    "repoFiles": typer.Option(default=..., help="Local path to the file or files to upload. Defaults to the relative path of the file of repo of OpenCSG Hub."),
    "revision": typer.Option(default=..., help="An optional Git revision id which can be a branch name"),
    "cache_dir": typer.Option(default=..., help="Path to the directory where to save the downloaded files."),
    "endpoint": typer.Option(default=..., help="The address of the request to be sent."),
    "token": typer.Option(default=..., help="A User Access Token generated from https://opencsg.com/settings/access-token"),
}

@app.command(name="download", help="Download model/dataset from opencsg.com")
def download(
        repo_id: Annotated[str, OPTIONS["repoID"]],
        repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL, 
        revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
        cache_dir: Annotated[Optional[str], OPTIONS["cache_dir"]] = None,
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
        repo_file: Annotated[List[str], OPTIONS["repoFiles"]],
        repo_type: Annotated[RepoType, OPTIONS["repoType"]] = RepoType.MODEL,
        revision: Annotated[Optional[str], OPTIONS["revision"]] = DEFAULT_REVISION,
        endpoint: Annotated[Optional[str], OPTIONS["endpoint"]] = DEFAULT_CSGHUB_DOMAIN,
        token: Annotated[Optional[str], OPTIONS["token"]] = None,
    ):
    repo.upload(
        repo_id=repo_id, 
        repo_type=repo_type, 
        repo_file=repo_file, 
        revision=revision, 
        endpoint=endpoint,
        token=token
    )

if __name__ == "__main__":
    app()
