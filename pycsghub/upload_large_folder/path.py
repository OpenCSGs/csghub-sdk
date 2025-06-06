from fnmatch import fnmatch
from pathlib import Path
from typing import Callable, Generator, Iterable, List, Optional, TypeVar, Union

T = TypeVar("T")

def filter_repo_objects(
    items: Iterable[T],
    *,
    allow_patterns: Optional[Union[List[str], str]] = None,
    ignore_patterns: Optional[Union[List[str], str]] = None,
    key: Optional[Callable[[T], str]] = None,
) -> Generator[T, None, None]:
    if isinstance(allow_patterns, str):
        allow_patterns = [allow_patterns]

    if isinstance(ignore_patterns, str):
        ignore_patterns = [ignore_patterns]

    if allow_patterns is not None:
        allow_patterns = [_add_wildcard_to_directories(p) for p in allow_patterns]
    if ignore_patterns is not None:
        ignore_patterns = [_add_wildcard_to_directories(p) for p in ignore_patterns]

    if key is None:

        def _identity(item: T) -> str:
            if isinstance(item, str):
                return item
            if isinstance(item, Path):
                return str(item)
            raise ValueError(f"please provide `key` argument in `filter_repo_objects`: `{item}` is not a string.")

        key = _identity

    for item in items:
        path = key(item)

        if allow_patterns is not None and not any(fnmatch(path, r) for r in allow_patterns):
            continue

        if ignore_patterns is not None and any(fnmatch(path, r) for r in ignore_patterns):
            continue

        yield item


def _add_wildcard_to_directories(pattern: str) -> str:
    if pattern[-1] == "/":
        return pattern + "*"
    return pattern
