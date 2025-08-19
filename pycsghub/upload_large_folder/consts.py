REPO_REGULAR_TYPE = "regular"
REPO_LFS_TYPE = "lfs"

COMMIT_ACTION_CREATE = "create"
COMMIT_ACTION_UPDATE = "update"
COMMIT_ACTION_DELETE = "delete"

KEY_MSG = "msg"
MSG_OK = "OK"
KEY_UPLOADID = "uploadId"

DEFAULT_IGNORE_PATTERNS = [
    ".git",
    ".git/*",
    "*/.git",
    "**/.git/**",
    ".cache/csghub",
    ".cache/csghub/*",
    "*/.cache/csghub",
    "**/.cache/csghub/**",
]

FORBIDDEN_FOLDERS = [".git", ".cache"]

# Timeout of aquiring file lock and logging the attempt
FILELOCK_LOG_EVERY_SECONDS = 10

WAITING_TIME_IF_NO_TASKS = 3  # seconds
MAX_NB_REGULAR_FILES_PER_COMMIT = 75
MAX_NB_LFS_FILES_PER_COMMIT = 150

META_FILE_IDENTIFIER = "version https://git-lfs.github.com/spec/v1"
META_FILE_OID_PREFIX = "oid sha256:"
