from enum import Enum
from pycsghub.constants import REPO_TYPE_MODEL, REPO_TYPE_DATASET, REPO_TYPE_SPACE, REPO_TYPE_CODE

class RepoType(str, Enum):
    MODEL = REPO_TYPE_MODEL
    DATASET = REPO_TYPE_DATASET
    SPACE = REPO_TYPE_SPACE
    CODE = REPO_TYPE_CODE
