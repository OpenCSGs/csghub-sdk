import typer
import os
from typing import Annotated, List, Optional
from pycsghub.cmd import repo
from pycsghub.cmd.repo_types import RepoType
from importlib.metadata import version
from pycsghub.constants import DEFAULT_CSGHUB_DOMAIN, DEFAULT_REVISION

app = typer.Typer(add_completion=False)

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
}

@app.command(name="download", help="Download model/dataset from opencsg.com")
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

@app.command(name="upload", help="Upload repository files to opencsg.com.")
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
 
@app.callback(invoke_without_command=True)
def main(version: bool = OPTIONS["version"]):
    pass

if __name__ == "__main__":
    app()
