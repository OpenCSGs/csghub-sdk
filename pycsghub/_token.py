import os
from pathlib import Path
from typing import Optional

from pycsghub.constants import CSGHUB_TOKEN_PATH


def _get_token_from_environment() -> Optional[str]:
    return _clean_token(os.environ.get("CSGHUB_TOKEN"))  # apk key


def _get_token_from_file() -> Optional[str]:
    try:
        return _clean_token(Path(CSGHUB_TOKEN_PATH).read_text())
    except FileNotFoundError:
        return None


def _clean_token(token: Optional[str]) -> Optional[str]:
    """Clean token by removing trailing and leading spaces and newlines.

    If token is an empty string, return None.
    """
    if token is None:
        return None
    return token.replace("\r", "").replace("\n", "").strip() or None
