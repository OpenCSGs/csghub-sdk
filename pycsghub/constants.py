import os
API_FILE_DOWNLOAD_CHUNK_SIZE = 1024 * 1024
API_FILE_DOWNLOAD_TIMEOUT = 5
API_FILE_DOWNLOAD_RETRY_TIMES = 5


CSG_HOME = os.environ.get('CSG_HOME', '/home')
CSG_TOKEN_PATH = os.environ.get("CSG_TOKEN_PATH", os.path.join(CSG_HOME, "token"))

MODEL_ID_SEPARATOR = '/'
DEFAULT_CSG_GROUP = 'OpenSCG'

DEFAULT_REVISION = "main"

FILE_HASH = 'Sha256'

CSG_URL_SCHEME = 'https://'
DEFAULT_CSG_DOMAIN = 'hub-stg.opencsg.com' #todo 待定
