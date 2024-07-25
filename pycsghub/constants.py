import os
from enum import Enum
API_FILE_DOWNLOAD_CHUNK_SIZE = 1024 * 1024
API_FILE_DOWNLOAD_TIMEOUT = 5
API_FILE_DOWNLOAD_RETRY_TIMES = 5

REPO_TYPE_DATASET = "dataset"
REPO_TYPE_MODEL = "model"
REPO_TYPE_SPACE = "space"
REPO_TYPES = [None, REPO_TYPE_MODEL, REPO_TYPE_DATASET]

CSGHUB_HOME = os.environ.get('CSGHUB_HOME', '/home')
CSGHUB_TOKEN_PATH = os.environ.get("CSGHUB_TOKEN_PATH", os.path.join(CSGHUB_HOME, "token"))

MODEL_ID_SEPARATOR = '/'
DEFAULT_CSG_GROUP = 'OpenCSG'

DEFAULT_REVISION = "main"

FILE_HASH = 'Sha256'

DEFAULT_CSGHUB_DOMAIN = 'https://hub.opencsg.com'


class MIRROR(str, Enum):
    AUTO = "auto"
    HF = "hf"
    CSGHUB = "csghub"
