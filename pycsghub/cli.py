import typer
from typing import Annotated, List
from pycsghub.cmd import model, dataset
from pycsghub.cmd.repo_types import RepoType

app = typer.Typer(add_completion=False)

OPTIONS = {
    "repoType": typer.Option(default=..., help="Specify the repository type."),
    "repoID": typer.Option(default=..., help="Specify the repository ID."),
    "files": typer.Option(default=..., help="Local path to the file or files. Defaults to the relative path of the file of repo of OpenCSG Hub.")
}

@app.command(name="download", help="Download model/dataset from OpenCSGS Hub")
def download(
    repo_type: Annotated[RepoType, OPTIONS["repoType"]], 
    repo_id: Annotated[str, OPTIONS["repoID"]]
    ):
    if repo_type == RepoType.MODEL:
        model.download(repo_id=repo_id)
    elif repo_type == RepoType.DATASET:
        dataset.download(repo_id=repo_id)
     
@app.command(name="create", help="Create model/dataset on OpenCSGS Hub.")
def create(
    repo_type: Annotated[RepoType, OPTIONS["repoType"]], 
    repo_id: Annotated[str, OPTIONS["repoID"]]
    ):
    if repo_type == RepoType.MODEL:
        model.create(repo_id=repo_id)
    elif repo_type == RepoType.DATASET:
        dataset.create(repo_id=repo_id)
        
@app.command(name="upload", help="Upload repository files to OpenCSGS Hub.")
def upload(
    repo_type: Annotated[RepoType, OPTIONS["repoType"]], 
    repo_id: Annotated[str, OPTIONS["repoID"]],
    repo_file: Annotated[List[str], OPTIONS["files"]]
    ):
    print("upload test", repo_type, repo_id, repo_file)

if __name__ == "__main__":
    app()
