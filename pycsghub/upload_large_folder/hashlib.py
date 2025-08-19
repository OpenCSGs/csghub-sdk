import functools
import sys

import hashlib

_kwargs = {"usedforsecurity": False} if sys.version_info >= (3, 9) else {}
md5 = functools.partial(hashlib.md5, **_kwargs)
sha1 = functools.partial(hashlib.sha1, **_kwargs)
sha256 = functools.partial(hashlib.sha256, **_kwargs)
