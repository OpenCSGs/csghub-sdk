from typing import Optional
from pathlib import Path
import os
from pycsghub.constants import CSGHUB_TOKEN_PATH


def _get_token_from_environment() -> Optional[str]:
    return _clean_token(os.environ.get("CSG_TOKEN")) # apk key 直接写入环境


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