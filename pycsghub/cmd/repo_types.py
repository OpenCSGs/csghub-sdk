import typer
from enum import Enum
from pycsghub.constants import REPO_TYPE_MODEL, REPO_TYPE_DATASET

class RepoType(str, Enum):
    MODEL = REPO_TYPE_MODEL
    DATASET = REPO_TYPE_DATASET
