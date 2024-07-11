import typer
from enum import Enum

class RepoType(Enum):
    MODEL = "model"
    DATASET = "dataset"
    SPACE = "space"